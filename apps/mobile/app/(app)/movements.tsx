import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  Pressable,
  RefreshControl,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { colors, radius, spacing, typography } from "@/design-system/tokens";
import { useAuth } from "@/features/auth/AuthContext";
import {
  createIdempotencyKey,
  formatMoney,
  formatMovementDate,
  parseCopAmount,
} from "@/features/transactions/format";
import type {
  Category,
  CreateTransactionInput,
  Transaction,
  TransactionPage,
  TransactionType,
} from "@/features/transactions/types";
import { ApiError } from "@/services/api";

type FormState = {
  type: TransactionType;
  amount: string;
  description: string;
  categoryId: string | null;
};

const EMPTY_FORM: FormState = {
  type: "expense",
  amount: "",
  description: "",
  categoryId: null,
};

export default function MovementsScreen() {
  const { authenticatedRequest, user } = useAuth();
  const [movements, setMovements] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingMovement, setEditingMovement] = useState<Transaction | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | TransactionType>("all");
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [dateFilter, setDateFilter] = useState<"all" | "month">("month");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const load = useCallback(
    async (isRefresh = false) => {
      isRefresh ? setRefreshing(true) : setLoading(true);
      setError(null);
      setOffline(false);
      try {
        const [page, availableCategories] = await Promise.all([
          authenticatedRequest<TransactionPage>("/transactions?limit=20"),
          authenticatedRequest<Category[]>("/categories"),
        ]);
        setMovements(page.items);
        setNextCursor(page.next_cursor);
        setCategories(availableCategories);
      } catch (reason) {
        setOffline(!(reason instanceof ApiError));
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Parece que no tienes conexión. Revisa tu red e inténtalo nuevamente.",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authenticatedRequest],
  );

  const loadMore = useCallback(async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await authenticatedRequest<TransactionPage>(
        `/transactions?limit=20&cursor=${encodeURIComponent(nextCursor)}`,
      );
      setMovements((current) => [
        ...current,
        ...page.items.filter(
          (movement) => !current.some((item) => item.id === movement.id),
        ),
      ]);
      setNextCursor(page.next_cursor);
      setOffline(false);
    } catch (reason) {
      setOffline(!(reason instanceof ApiError));
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Sin conexión. Conservamos los movimientos ya cargados.",
      );
    } finally {
      setLoadingMore(false);
    }
  }, [authenticatedRequest, loadingMore, nextCursor]);

  useEffect(() => {
    void load();
  }, [load]);

  const visibleCategories = useMemo(
    () =>
      categories.filter(
        (category) =>
          category.movement_scope === "both" ||
          category.movement_scope === form.type,
      ),
    [categories, form.type],
  );

  const visibleMovements = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("es");
    const monthStart = new Date();
    monthStart.setDate(1);
    monthStart.setHours(0, 0, 0, 0);
    return movements.filter((movement) => {
      const matchesType = typeFilter === "all" || movement.type === typeFilter;
      const matchesCategory =
        categoryFilter === null || movement.category_id === categoryFilter;
      const matchesDate =
        dateFilter === "all" || new Date(movement.occurred_at) >= monthStart;
      const category = categories.find(
        (candidate) => candidate.id === movement.category_id,
      );
      const searchable = `${movement.description} ${category?.name ?? ""}`.toLocaleLowerCase(
        "es",
      );
      return (
        matchesType &&
        matchesCategory &&
        matchesDate &&
        (!normalizedQuery || searchable.includes(normalizedQuery))
      );
    });
  }, [categories, categoryFilter, dateFilter, movements, query, typeFilter]);

  function openForm() {
    setEditingMovement(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setFormOpen(true);
  }

  function openMovement(movement: Transaction) {
    setEditingMovement(movement);
    setForm({
      type: movement.type,
      amount: String(movement.amount_minor),
      description: movement.description,
      categoryId: movement.category_id,
    });
    setFormError(null);
    setFormOpen(true);
  }

  async function saveMovement() {
    const amount = parseCopAmount(form.amount);
    if (!amount) {
      setFormError("Ingresa un monto válido mayor que cero.");
      return;
    }

    setSaving(true);
    setFormError(null);
    const payload: CreateTransactionInput = {
      type: form.type,
      amount_minor: amount,
      currency: user?.default_currency ?? "COP",
      category_id: form.categoryId,
      description: form.description.trim(),
      occurred_at: new Date().toISOString(),
      source: "manual",
    };

    try {
      const movement = editingMovement
        ? await authenticatedRequest<Transaction>(
            `/transactions/${editingMovement.id}`,
            {
              method: "PATCH",
              body: JSON.stringify({
                type: payload.type,
                amount_minor: payload.amount_minor,
                category_id: payload.category_id,
                description: payload.description,
              }),
            },
          )
        : await authenticatedRequest<Transaction>("/transactions", {
            method: "POST",
            headers: { "Idempotency-Key": createIdempotencyKey() },
            body: JSON.stringify(payload),
          });
      setMovements((current) =>
        editingMovement
          ? current.map((item) => (item.id === movement.id ? movement : item))
          : [movement, ...current],
      );
      setFormOpen(false);
      setEditingMovement(null);
    } catch (reason) {
      setFormError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos guardar el movimiento.",
      );
    } finally {
      setSaving(false);
    }
  }

  function confirmDelete() {
    if (!editingMovement) return;
    Alert.alert(
      "Eliminar movimiento",
      "El movimiento dejará de aparecer en tu historial. Podrá restaurarse desde la API.",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Eliminar",
          style: "destructive",
          onPress: () => void deleteMovement(editingMovement.id),
        },
      ],
    );
  }

  async function deleteMovement(id: string) {
    setSaving(true);
    setFormError(null);
    try {
      await authenticatedRequest<void>(`/transactions/${id}`, { method: "DELETE" });
      setMovements((current) => current.filter((movement) => movement.id !== id));
      setFormOpen(false);
      setEditingMovement(null);
    } catch (reason) {
      setFormError(
        reason instanceof ApiError
          ? reason.message
          : "No pudimos eliminar el movimiento.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <View>
          <Text style={styles.eyebrow}>TU HISTORIAL</Text>
          <Text style={styles.title}>Movimientos</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Registrar movimiento"
          onPress={openForm}
          style={({ pressed }) => [styles.addButton, pressed && styles.pressed]}
        >
          <Text style={styles.addButtonText}>＋</Text>
        </Pressable>
      </View>

      {!loading && !error ? (
        <View style={styles.filters}>
          <TextInput
            accessibilityLabel="Buscar movimientos"
            onChangeText={setQuery}
            placeholder="Buscar por descripción o categoría"
            placeholderTextColor={colors.muted}
            style={styles.searchInput}
            value={query}
          />
          <View style={styles.filterRow}>
            {(
              [
                ["all", "Todos"],
                ["expense", "Gastos"],
                ["income", "Ingresos"],
              ] as const
            ).map(([value, label]) => (
              <Pressable
                key={value}
                onPress={() => setTypeFilter(value)}
                style={[
                  styles.filterChip,
                  typeFilter === value && styles.filterChipActive,
                ]}
              >
                <Text
                  style={[
                    styles.filterText,
                    typeFilter === value && styles.filterTextActive,
                  ]}
                >
                  {label}
                </Text>
              </Pressable>
            ))}
          </View>
          <View style={styles.filterRow}>
            {(
              [
                ["month", "Este mes"],
                ["all", "Cualquier fecha"],
              ] as const
            ).map(([value, label]) => (
              <Pressable
                key={value}
                onPress={() => setDateFilter(value)}
                style={[
                  styles.filterChip,
                  dateFilter === value && styles.filterChipActive,
                ]}
              >
                <Text
                  style={[
                    styles.filterText,
                    dateFilter === value && styles.filterTextActive,
                  ]}
                >
                  {label}
                </Text>
              </Pressable>
            ))}
          </View>
          <ScrollView
            contentContainerStyle={styles.categoryFilters}
            horizontal
            showsHorizontalScrollIndicator={false}
          >
            <Pressable
              onPress={() => setCategoryFilter(null)}
              style={[
                styles.filterChip,
                categoryFilter === null && styles.filterChipActive,
              ]}
            >
              <Text
                style={[
                  styles.filterText,
                  categoryFilter === null && styles.filterTextActive,
                ]}
              >
                Todas las categorías
              </Text>
            </Pressable>
            {categories.map((category) => (
              <Pressable
                key={category.id}
                onPress={() => setCategoryFilter(category.id)}
                style={[
                  styles.filterChip,
                  categoryFilter === category.id && styles.filterChipActive,
                ]}
              >
                <Text
                  style={[
                    styles.filterText,
                    categoryFilter === category.id && styles.filterTextActive,
                  ]}
                >
                  {category.name}
                </Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      ) : null}

      {offline && movements.length ? (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>Sin conexión · mostrando datos cargados</Text>
        </View>
      ) : null}

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} size="large" />
          <Text style={styles.muted}>Cargando movimientos…</Text>
        </View>
      ) : error && movements.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.errorTitle}>
            {offline ? "Estás sin conexión" : "No pudimos cargar tus datos"}
          </Text>
          <Text style={styles.muted}>{error}</Text>
          <Pressable onPress={() => void load()} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>Reintentar</Text>
          </Pressable>
        </View>
      ) : (
        <FlatList
          contentContainerStyle={[
            styles.list,
            visibleMovements.length === 0 && styles.emptyList,
          ]}
          data={visibleMovements}
          keyExtractor={(item) => item.id}
          onEndReached={() => void loadMore()}
          onEndReachedThreshold={0.35}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              tintColor={colors.primary}
              onRefresh={() => void load(true)}
            />
          }
          renderItem={({ item }) => (
            <MovementRow
              movement={item}
              category={categories.find((category) => category.id === item.category_id)}
              onPress={() => openMovement(item)}
            />
          )}
          ListFooterComponent={
            loadingMore ? (
              <ActivityIndicator color={colors.primary} style={styles.listFooter} />
            ) : null
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <View style={styles.emptyIcon}>
                <Text style={styles.emptyIconText}>$</Text>
              </View>
              <Text style={styles.errorTitle}>
                {movements.length ? "No encontramos coincidencias" : "Aún no hay movimientos"}
              </Text>
              <Text style={styles.muted}>
                {movements.length
                  ? "Prueba con otra búsqueda o cambia los filtros."
                  : "Registra tu primer ingreso o gasto para comenzar."}
              </Text>
              {!movements.length ? (
                <Pressable onPress={openForm} style={styles.primaryButton}>
                  <Text style={styles.primaryButtonText}>Registrar movimiento</Text>
                </Pressable>
              ) : null}
            </View>
          }
        />
      )}

      <MovementForm
        categories={visibleCategories}
        form={form}
        formError={formError}
        editing={Boolean(editingMovement)}
        open={formOpen}
        saving={saving}
        onChange={setForm}
        onClose={() => {
          if (!saving) {
            setFormOpen(false);
            setEditingMovement(null);
          }
        }}
        onDelete={confirmDelete}
        onSave={() => void saveMovement()}
      />
    </SafeAreaView>
  );
}

function MovementRow({
  movement,
  category,
  onPress,
}: {
  movement: Transaction;
  category?: Category;
  onPress(): void;
}) {
  const isIncome = movement.type === "income";
  return (
    <Pressable
      accessibilityHint="Abre el detalle y permite editar"
      onPress={onPress}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}
    >
      <View style={[styles.typeIcon, isIncome && styles.incomeIcon]}>
        <Text style={styles.typeIconText}>{isIncome ? "↓" : "↑"}</Text>
      </View>
      <View style={styles.rowBody}>
        <Text numberOfLines={1} style={styles.rowTitle}>
          {movement.description || category?.name || "Sin descripción"}
        </Text>
        <Text style={styles.rowMeta}>
          {category?.name ?? "Sin categoría"} · {formatMovementDate(movement.occurred_at)}
        </Text>
      </View>
      <Text style={[styles.rowAmount, isIncome && styles.incomeAmount]}>
        {isIncome ? "+" : "−"}
        {formatMoney(movement.amount_minor, movement.currency)}
      </Text>
    </Pressable>
  );
}

type MovementFormProps = {
  open: boolean;
  form: FormState;
  categories: Category[];
  saving: boolean;
  formError: string | null;
  editing: boolean;
  onChange(value: FormState): void;
  onClose(): void;
  onDelete(): void;
  onSave(): void;
};

function MovementForm({
  open,
  form,
  categories,
  saving,
  formError,
  editing,
  onChange,
  onClose,
  onDelete,
  onSave,
}: MovementFormProps) {
  return (
    <Modal animationType="slide" onRequestClose={onClose} transparent visible={open}>
      <View style={styles.modalBackdrop}>
        <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>
              {editing ? "Editar movimiento" : "Nuevo movimiento"}
            </Text>
            <Pressable accessibilityLabel="Cerrar" onPress={onClose}>
              <Text style={styles.close}>×</Text>
            </Pressable>
          </View>
          <ScrollView keyboardShouldPersistTaps="handled">
            <View style={styles.segment}>
              {(["expense", "income"] as const).map((type) => (
                <Pressable
                  key={type}
                  onPress={() =>
                    onChange({ ...form, type, categoryId: null })
                  }
                  style={[
                    styles.segmentOption,
                    form.type === type && styles.segmentOptionActive,
                  ]}
                >
                  <Text
                    style={[
                      styles.segmentText,
                      form.type === type && styles.segmentTextActive,
                    ]}
                  >
                    {type === "expense" ? "Gasto" : "Ingreso"}
                  </Text>
                </Pressable>
              ))}
            </View>

            <Text style={styles.fieldLabel}>MONTO</Text>
            <View style={styles.amountField}>
              <Text style={styles.currency}>$</Text>
              <TextInput
                accessibilityLabel="Monto"
                inputMode="numeric"
                onChangeText={(amount) => onChange({ ...form, amount })}
                placeholder="0"
                placeholderTextColor={colors.muted}
                style={styles.amountInput}
                value={form.amount}
              />
              <Text style={styles.currencyCode}>COP</Text>
            </View>

            <Text style={styles.fieldLabel}>DESCRIPCIÓN</Text>
            <TextInput
              accessibilityLabel="Descripción"
              maxLength={240}
              onChangeText={(description) => onChange({ ...form, description })}
              placeholder="Ej. Almuerzo"
              placeholderTextColor={colors.muted}
              style={styles.textInput}
              value={form.description}
            />

            <Text style={styles.fieldLabel}>CATEGORÍA</Text>
            <View style={styles.categoryList}>
              {categories.map((category) => (
                <Pressable
                  key={category.id}
                  onPress={() => onChange({ ...form, categoryId: category.id })}
                  style={[
                    styles.categoryChip,
                    form.categoryId === category.id && styles.categoryChipActive,
                  ]}
                >
                  <Text
                    style={[
                      styles.categoryText,
                      form.categoryId === category.id && styles.categoryTextActive,
                    ]}
                  >
                    {category.name}
                  </Text>
                </Pressable>
              ))}
            </View>

            {formError ? <Text style={styles.formError}>{formError}</Text> : null}
            <Pressable
              disabled={saving}
              onPress={onSave}
              style={[styles.primaryButton, saving && styles.disabled]}
            >
              {saving ? (
                <ActivityIndicator color={colors.surface} />
              ) : (
                <Text style={styles.primaryButtonText}>
                  {editing ? "Guardar cambios" : "Guardar movimiento"}
                </Text>
              )}
            </Pressable>
            {editing ? (
              <Pressable
                disabled={saving}
                onPress={onDelete}
                style={styles.deleteButton}
              >
                <Text style={styles.deleteButtonText}>Eliminar movimiento</Text>
              </Pressable>
            ) : null}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.background },
  header: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
  },
  eyebrow: { ...typography.label, color: colors.olive },
  title: { ...typography.title, color: colors.ink, marginTop: spacing.xs },
  addButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.round,
    height: 48,
    justifyContent: "center",
    width: 48,
  },
  addButtonText: { color: colors.surface, fontSize: 27, lineHeight: 30 },
  pressed: { opacity: 0.8 },
  filters: { paddingHorizontal: spacing.md, paddingBottom: spacing.sm },
  searchInput: {
    ...typography.body,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.ink,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
  },
  filterRow: {
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  categoryFilters: {
    gap: spacing.sm,
    paddingRight: spacing.md,
    paddingTop: spacing.sm,
  },
  filterChip: {
    borderColor: colors.border,
    borderRadius: radius.round,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  filterChipActive: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
  },
  filterText: { ...typography.caption, color: colors.muted },
  filterTextActive: { color: colors.primary, fontWeight: "700" },
  offlineBanner: {
    backgroundColor: "#F1EBDD",
    borderRadius: radius.sm,
    marginHorizontal: spacing.md,
    padding: spacing.sm,
  },
  offlineText: {
    ...typography.caption,
    color: colors.ink,
    textAlign: "center",
  },
  center: {
    alignItems: "center",
    gap: spacing.md,
    justifyContent: "center",
    padding: spacing.xl,
  },
  list: { padding: spacing.md, paddingBottom: 100 },
  listFooter: { padding: spacing.lg },
  emptyList: { flexGrow: 1, justifyContent: "center" },
  muted: {
    ...typography.body,
    color: colors.muted,
    textAlign: "center",
  },
  errorTitle: { ...typography.cardValue, color: colors.ink, textAlign: "center" },
  row: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flexDirection: "row",
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  typeIcon: {
    alignItems: "center",
    backgroundColor: "#F5EAEA",
    borderRadius: radius.round,
    height: 40,
    justifyContent: "center",
    width: 40,
  },
  incomeIcon: { backgroundColor: colors.primarySoft },
  typeIconText: { color: colors.primary, fontSize: 20, fontWeight: "700" },
  rowBody: { flex: 1, marginHorizontal: spacing.md },
  rowTitle: { ...typography.cardValue, color: colors.ink },
  rowMeta: { ...typography.caption, color: colors.muted, marginTop: spacing.xs },
  rowAmount: { color: colors.danger, fontSize: 14, fontWeight: "700" },
  incomeAmount: { color: colors.primary },
  emptyIcon: {
    alignItems: "center",
    backgroundColor: colors.primarySoft,
    borderRadius: radius.round,
    height: 64,
    justifyContent: "center",
    width: 64,
  },
  emptyIconText: { color: colors.primary, fontSize: 28, fontWeight: "700" },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: radius.sm,
    justifyContent: "center",
    minHeight: 50,
    paddingHorizontal: spacing.lg,
  },
  primaryButtonText: { ...typography.button, color: colors.surface },
  secondaryButton: {
    borderColor: colors.primary,
    borderRadius: radius.sm,
    borderWidth: 1,
    paddingHorizontal: spacing.lg,
    paddingVertical: 12,
  },
  secondaryButtonText: { ...typography.button, color: colors.primary },
  modalBackdrop: {
    backgroundColor: "rgba(32, 38, 36, 0.35)",
    flex: 1,
    justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: colors.background,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    maxHeight: "92%",
    padding: spacing.lg,
  },
  sheetHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.lg,
  },
  sheetTitle: { ...typography.title, color: colors.ink, fontSize: 24 },
  close: { color: colors.muted, fontSize: 32, lineHeight: 32 },
  segment: {
    backgroundColor: colors.border,
    borderRadius: radius.sm,
    flexDirection: "row",
    marginBottom: spacing.lg,
    padding: 3,
  },
  segmentOption: {
    alignItems: "center",
    borderRadius: 8,
    flex: 1,
    paddingVertical: 11,
  },
  segmentOptionActive: { backgroundColor: colors.surface },
  segmentText: { ...typography.button, color: colors.muted },
  segmentTextActive: { color: colors.primary },
  fieldLabel: {
    ...typography.label,
    color: colors.muted,
    marginBottom: spacing.sm,
    marginTop: spacing.md,
  },
  amountField: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 1,
    flexDirection: "row",
    paddingHorizontal: spacing.md,
  },
  currency: { ...typography.amount, color: colors.ink },
  amountInput: {
    ...typography.amount,
    color: colors.ink,
    flex: 1,
    padding: spacing.md,
  },
  currencyCode: { ...typography.label, color: colors.muted },
  textInput: {
    ...typography.body,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.sm,
    borderWidth: 1,
    color: colors.ink,
    padding: spacing.md,
  },
  categoryList: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  categoryChip: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radius.round,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  categoryChipActive: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
  },
  categoryText: { ...typography.caption, color: colors.ink },
  categoryTextActive: { color: colors.primary, fontWeight: "700" },
  formError: {
    ...typography.caption,
    color: colors.danger,
    marginBottom: spacing.md,
    textAlign: "center",
  },
  disabled: { opacity: 0.55 },
  deleteButton: {
    alignItems: "center",
    marginTop: spacing.sm,
    padding: spacing.md,
  },
  deleteButtonText: { ...typography.button, color: colors.danger },
});
