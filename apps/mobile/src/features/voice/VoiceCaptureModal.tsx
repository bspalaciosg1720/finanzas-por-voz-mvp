import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import {
  RecordingPresets,
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from "expo-audio";
import { File } from "expo-file-system";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import { useAuth } from "@/features/auth/AuthContext";
import {
  createIdempotencyKey,
  parseCopAmount,
} from "@/features/transactions/format";
import type {
  Category,
  Transaction,
  TransactionType,
} from "@/features/transactions/types";
import type {
  AudioTranscription,
  VoiceInterpretation,
} from "@/features/voice/types";
import { ApiError } from "@/services/api";

const MAX_DURATION_SECONDS = 15;
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

export function VoiceCaptureModal({
  visible,
  onClose,
}: {
  visible: boolean;
  onClose(): void;
}) {
  const { authenticatedRequest, user } = useAuth();
  const recorder = useAudioRecorder({
    ...RecordingPresets.HIGH_QUALITY,
    directory: "cache",
  });
  const recorderState = useAudioRecorderState(recorder, 200);
  const [recordedUri, setRecordedUri] = useState<string | null>(null);
  const [transcriptReady, setTranscriptReady] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interpretation, setInterpretation] =
    useState<VoiceInterpretation | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [movementType, setMovementType] =
    useState<TransactionType>("expense");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [occurredAt, setOccurredAt] = useState(new Date().toISOString());
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [interactionStartedAt, setInteractionStartedAt] = useState<number | null>(
    null,
  );

  useEffect(() => {
    if (
      recorderState.isRecording &&
      recorderState.durationMillis >= MAX_DURATION_SECONDS * 1000
    ) {
      void stopRecording();
    }
  });

  async function removeTemporaryAudio(targetUri = recordedUri) {
    if (!targetUri) return;
    try {
      const file = new File(targetUri);
      if (file.exists) file.delete();
    } finally {
      setRecordedUri(null);
    }
  }

  async function startRecording() {
    setBusy(true);
    setMessage(null);
    setInterpretation(null);
    setTranscript("");
    setTranscriptReady(false);
    await removeTemporaryAudio();
    try {
      const permission = await requestRecordingPermissionsAsync();
      if (!permission.granted) {
        setMessage(
          permission.canAskAgain
            ? "Necesitamos permiso para usar el micrófono."
            : "Activa el micrófono desde los ajustes del dispositivo.",
        );
        return;
      }
      await setAudioModeAsync({
        allowsRecording: true,
        playsInSilentMode: true,
        shouldPlayInBackground: false,
      });
      await recorder.prepareToRecordAsync();
      recorder.record({ forDuration: MAX_DURATION_SECONDS });
    } catch {
      setMessage("No fue posible iniciar la grabación.");
    } finally {
      setBusy(false);
    }
  }

  async function stopRecording() {
    if (!recorderState.isRecording) return;
    setBusy(true);
    try {
      await recorder.stop();
      const uri = recorder.uri;
      if (!uri) {
        setMessage("La grabación terminó sin generar un archivo.");
        return;
      }
      const file = new File(uri);
      if (file.size > MAX_FILE_SIZE_BYTES) {
        file.delete();
        setMessage("La grabación supera el límite de 5 MB. Intenta nuevamente.");
        return;
      }
      setRecordedUri(uri);
      await setAudioModeAsync({ allowsRecording: false });
      setTranscriptReady(true);
      await transcribeAudio(uri);
    } catch {
      setMessage("No fue posible finalizar la grabación.");
    } finally {
      setBusy(false);
    }
  }

  async function transcribeAudio(uri: string) {
    const contentType = uri.toLowerCase().endsWith(".webm")
      ? "audio/webm"
      : "audio/m4a";
    const form = new FormData();
    form.append(
      "file",
      {
        uri,
        name: contentType === "audio/webm" ? "recording.webm" : "recording.m4a",
        type: contentType,
      } as unknown as Blob,
    );
    try {
      const result = await authenticatedRequest<AudioTranscription>(
        "/voice/transcriptions",
        { method: "POST", body: form },
      );
      setTranscript(result.transcript);
      setMessage(null);
    } catch (reason) {
      setMessage(
        reason instanceof ApiError && reason.status === 503
          ? "La transcripción automática aún no está configurada. Escribe el texto para continuar."
          : reason instanceof ApiError
            ? reason.message
            : "No pudimos transcribir el audio. Puedes escribir el texto.",
      );
    } finally {
      await removeTemporaryAudio(uri);
    }
  }

  async function interpretTranscript() {
    if (!transcript.trim()) {
      setMessage("Escribe o corrige la transcripción.");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const [result, availableCategories] = await Promise.all([
        authenticatedRequest<VoiceInterpretation>("/voice/interpretations", {
          method: "POST",
          body: JSON.stringify({
            transcript,
            reference_at: new Date().toISOString(),
          }),
        }),
        authenticatedRequest<Category[]>("/categories"),
      ]);
      setInterpretation(result);
      setInteractionStartedAt(Date.now());
      setCategories(availableCategories);
      setMovementType(result.movement_type ?? "expense");
      setAmount(result.amount_minor ? String(result.amount_minor) : "");
      setDescription(result.description);
      setCategoryId(result.category_id);
      setOccurredAt(result.occurred_at);
    } catch (reason) {
      setMessage(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos interpretar el texto.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    if (!interpretation) return;
    const amountMinor = parseCopAmount(amount);
    if (!amountMinor) {
      setMessage("Corrige el monto antes de guardar.");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await authenticatedRequest<Transaction>("/transactions", {
        method: "POST",
        headers: { "Idempotency-Key": createIdempotencyKey() },
        body: JSON.stringify({
          type: movementType,
          amount_minor: amountMinor,
          currency: user?.default_currency ?? "COP",
          category_id: categoryId,
          description: description.trim(),
          occurred_at: occurredAt,
          source: "voice",
        }),
      });
      const correctedFields = [
        interpretation.amount_minor !== amountMinor ? "amount" : null,
        interpretation.movement_type !== movementType ? "movement_type" : null,
        interpretation.category_id !== categoryId ? "category" : null,
        interpretation.description !== description.trim() ? "description" : null,
        interpretation.occurred_at !== occurredAt ? "occurred_at" : null,
      ].filter((field): field is string => field !== null);
      try {
        await authenticatedRequest<void>(
          `/voice/interactions/${interpretation.interaction_id}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              outcome: "completed",
              corrected_fields: correctedFields,
              duration_ms: interactionStartedAt
                ? Date.now() - interactionStartedAt
                : null,
            }),
          },
        );
      } catch {
        // Telemetry must never prevent or duplicate a financial movement.
      }
      await close(true);
    } catch (reason) {
      setMessage(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos guardar el movimiento.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function close(skipAbandon = false) {
    if (recorderState.isRecording) await recorder.stop();
    await setAudioModeAsync({ allowsRecording: false });
    await removeTemporaryAudio();
    if (interpretation && !skipAbandon) {
      try {
        await authenticatedRequest<void>(
          `/voice/interactions/${interpretation.interaction_id}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              outcome: "abandoned",
              corrected_fields: [],
              duration_ms: interactionStartedAt
                ? Date.now() - interactionStartedAt
                : null,
            }),
          },
        );
      } catch {
        // Abandonment metrics are best effort and contain no financial content.
      }
    }
    setTranscript("");
    setTranscriptReady(false);
    setInterpretation(null);
    setInteractionStartedAt(null);
    setMessage(null);
    onClose();
  }

  const title = recorderState.isRecording
    ? "Te escuchamos…"
    : interpretation
      ? "Confirma los datos"
      : recordedUri || transcriptReady
        ? "Revisa la transcripción"
        : "Registra un movimiento";

  return (
    <Modal
      animationType="fade"
      onRequestClose={() => void close()}
      transparent
      visible={visible}
    >
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <ScrollView
            contentContainerStyle={styles.content}
            keyboardShouldPersistTaps="handled"
          >
            <Text style={styles.eyebrow}>REGISTRO POR VOZ</Text>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.help}>
              {interpretation
                ? "Nada se guardará hasta que confirmes."
                : recordedUri || transcriptReady
                  ? "La transcripción automática requiere configurar un proveedor. Puedes escribirla para completar y probar el flujo."
                  : 'Di “Gasté 18 mil en almuerzo”. Máximo 15 segundos.'}
            </Text>

            {!interpretation ? (
              <>
                <View
                  accessibilityLabel={
                    recorderState.isRecording
                      ? "Grabación de voz en curso"
                      : "Micrófono listo"
                  }
                  accessibilityRole="image"
                  style={[
                    styles.mic,
                    recorderState.isRecording && styles.micRecording,
                  ]}
                >
                  <Text style={styles.micIcon}>
                    {recorderState.isRecording ? "■" : "●"}
                  </Text>
                </View>
                <Text style={styles.timer}>
                  {Math.min(
                    MAX_DURATION_SECONDS,
                    Math.floor(recorderState.durationMillis / 1000),
                  )}
                  s / {MAX_DURATION_SECONDS}s
                </Text>
              </>
            ) : null}

            {message ? <Text style={styles.error}>{message}</Text> : null}
            {busy ? (
              <ActivityIndicator color={colors.primary} style={styles.action} />
            ) : interpretation ? (
              <ConfirmationFields
                amount={amount}
                categories={categories}
                categoryId={categoryId}
                description={description}
                interpretation={interpretation}
                movementType={movementType}
                onAmount={setAmount}
                onCategory={setCategoryId}
                onDescription={setDescription}
                onMovementType={setMovementType}
                occurredAt={occurredAt}
                onOccurredAt={setOccurredAt}
                onSave={() => void save()}
              />
            ) : recorderState.isRecording ? (
              <Action label="Terminar grabación" onPress={() => void stopRecording()} />
            ) : recordedUri || transcriptReady ? (
              <View style={styles.fullWidth}>
                <Text style={styles.fieldLabel}>TRANSCRIPCIÓN EDITABLE</Text>
                <TextInput
                  accessibilityLabel="Transcripción editable"
                  multiline
                  onChangeText={setTranscript}
                  placeholder="Ej. Gasté 18 mil en almuerzo"
                  placeholderTextColor={colors.muted}
                  style={[styles.input, styles.transcriptInput]}
                  value={transcript}
                />
                <Action
                  label="Interpretar texto"
                  onPress={() => void interpretTranscript()}
                />
                <Pressable onPress={() => void startRecording()} style={styles.link}>
                  <Text style={styles.linkText}>Grabar nuevamente</Text>
                </Pressable>
              </View>
            ) : (
              <Action
                label="Comenzar a grabar"
                onPress={() => void startRecording()}
              />
            )}

            <Pressable onPress={() => void close()} style={styles.link}>
              <Text style={styles.linkText}>Cancelar y eliminar audio</Text>
            </Pressable>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

function ConfirmationFields({
  amount,
  categories,
  categoryId,
  description,
  interpretation,
  movementType,
  occurredAt,
  onAmount,
  onCategory,
  onDescription,
  onMovementType,
  onOccurredAt,
  onSave,
}: {
  amount: string;
  categories: Category[];
  categoryId: string | null;
  description: string;
  interpretation: VoiceInterpretation;
  movementType: TransactionType;
  occurredAt: string;
  onAmount(value: string): void;
  onCategory(value: string): void;
  onDescription(value: string): void;
  onMovementType(value: TransactionType): void;
  onOccurredAt(value: string): void;
  onSave(): void;
}) {
  return (
    <View style={styles.fullWidth}>
      <View style={styles.segment}>
        {(["expense", "income"] as const).map((type) => (
          <Pressable
            key={type}
            onPress={() => onMovementType(type)}
            style={[
              styles.segmentOption,
              movementType === type && styles.segmentActive,
            ]}
          >
            <Text style={styles.segmentText}>
              {type === "expense" ? "Gasto" : "Ingreso"}
            </Text>
          </Pressable>
        ))}
      </View>
      <Text style={styles.fieldLabel}>MONTO</Text>
      <TextInput
        accessibilityLabel="Monto interpretado"
        inputMode="numeric"
        onChangeText={onAmount}
        style={styles.input}
        value={amount}
      />
      <Text style={styles.fieldLabel}>DESCRIPCIÓN</Text>
      <TextInput
        accessibilityLabel="Descripción interpretada"
        maxLength={240}
        onChangeText={onDescription}
        style={styles.input}
        value={description}
      />
      <Text style={styles.fieldLabel}>CATEGORÍA</Text>
      <View style={styles.categoryList}>
        {categories
          .filter(
            (category) =>
              category.movement_scope === "both" ||
              category.movement_scope === movementType,
          )
          .map((category) => (
            <Pressable
              accessibilityRole="button"
              key={category.id}
              onPress={() => onCategory(category.id)}
              style={[
                styles.category,
                categoryId === category.id && styles.categoryActive,
              ]}
            >
              <Text style={styles.categoryText}>{category.name}</Text>
            </Pressable>
          ))}
      </View>
      <Text style={styles.fieldLabel}>FECHA Y HORA</Text>
      <Text style={styles.dateText}>
        {new Intl.DateTimeFormat("es-CO", {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(new Date(occurredAt))}
      </Text>
      <View style={styles.dateOptions}>
        <Pressable
          onPress={() => onOccurredAt(new Date().toISOString())}
          style={styles.dateOption}
        >
          <Text style={styles.dateOptionText}>Ahora</Text>
        </Pressable>
        <Pressable
          onPress={() => {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            onOccurredAt(yesterday.toISOString());
          }}
          style={styles.dateOption}
        >
          <Text style={styles.dateOptionText}>Ayer</Text>
        </Pressable>
        <Pressable
          onPress={() => onOccurredAt(interpretation.occurred_at)}
          style={styles.dateOption}
        >
          <Text style={styles.dateOptionText}>Interpretada</Text>
        </Pressable>
      </View>
      {interpretation.ambiguities.length ? (
        <Text style={styles.warning}>
          Revisa: {interpretation.ambiguities.join(", ")}.
        </Text>
      ) : null}
      <Action label="Confirmar y guardar" onPress={onSave} />
    </View>
  );
}

function Action({ label, onPress }: { label: string; onPress(): void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.action}>
      <Text style={styles.actionText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    backgroundColor: "rgba(32, 38, 36, 0.45)",
    flex: 1,
    justifyContent: "center",
    padding: spacing.lg,
  },
  card: {
    backgroundColor: colors.background,
    borderRadius: radius.lg,
    maxHeight: "92%",
    overflow: "hidden",
  },
  content: { alignItems: "center", padding: spacing.lg },
  eyebrow: { ...typography.label, color: colors.olive },
  title: {
    ...typography.title,
    color: colors.ink,
    fontSize: 24,
    marginTop: spacing.sm,
    textAlign: "center",
  },
  help: {
    ...typography.body,
    color: colors.muted,
    marginTop: spacing.md,
    textAlign: "center",
  },
  mic: {
    alignItems: "center",
    backgroundColor: colors.primarySoft,
    borderRadius: radius.round,
    height: 92,
    justifyContent: "center",
    marginTop: spacing.xl,
    width: 92,
  },
  micRecording: { backgroundColor: "#F5EAEA" },
  micIcon: { color: colors.primary, fontSize: 30 },
  timer: {
    ...typography.cardValue,
    color: colors.ink,
    marginTop: spacing.md,
  },
  error: {
    ...typography.caption,
    color: colors.danger,
    marginTop: spacing.md,
    textAlign: "center",
  },
  fullWidth: { marginTop: spacing.md, width: "100%" },
  action: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.sm,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: 50,
    width: "100%",
  },
  actionText: { ...typography.button, color: colors.surface },
  link: { alignItems: "center", padding: spacing.md },
  linkText: { ...typography.button, color: colors.muted },
  fieldLabel: {
    ...typography.label,
    color: colors.muted,
    marginBottom: spacing.xs,
    marginTop: spacing.sm,
  },
  input: {
    ...typography.body,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.ink,
    padding: spacing.md,
  },
  transcriptInput: { minHeight: 82, textAlignVertical: "top" },
  segment: {
    backgroundColor: colors.border,
    borderRadius: radius.sm,
    flexDirection: "row",
    padding: 3,
  },
  segmentOption: {
    alignItems: "center",
    borderRadius: 8,
    flex: 1,
    padding: spacing.sm,
  },
  segmentActive: { backgroundColor: colors.surface },
  segmentText: { ...typography.button, color: colors.primary },
  categoryList: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  category: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.round,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  categoryActive: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
  },
  categoryText: { ...typography.caption, color: colors.ink },
  dateText: { ...typography.caption, color: colors.muted, marginTop: spacing.md },
  dateOptions: { flexDirection: "row", gap: spacing.xs, marginTop: spacing.sm },
  dateOption: {
    borderColor: colors.border,
    borderRadius: radius.round,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  dateOptionText: { ...typography.caption, color: colors.primary },
  warning: {
    ...typography.caption,
    color: colors.danger,
    marginTop: spacing.md,
  },
});
