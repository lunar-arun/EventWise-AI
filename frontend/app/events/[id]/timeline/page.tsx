import { TimelineClient } from "@/components/timeline/TimelineClient";

export default function EventTimelinePage({
  params,
}: {
  params: { id: string };
}) {
  const eventId = Number(params.id);
  return <TimelineClient eventId={eventId} />;
}
