type Params = {
  eventId: string;
  customerId: string;
};

type MemberRecord = {
  plan: "free" | "pro";
};

const processedEventIds = new Set<string>();
const memberStore = new Map<string, MemberRecord>([
  ["cus_demo_001", { plan: "free" }],
]);

export async function applySubscriptionUpdate({
  eventId,
  customerId,
}: Params): Promise<void> {
  // event.id で重複排除。同一イベントの二重適用を防ぐ
  if (processedEventIds.has(eventId)) {
    return;
  }

  const member = memberStore.get(customerId);

  if (!member) {
    throw new Error("member_not_found");
  }

  // checkout.session.completed 単体で完結させる。配信順の前後に依存しない
  member.plan = "pro";
  processedEventIds.add(eventId);
}
