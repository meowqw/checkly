import { Card, CardContent } from "@/components/ui/card";

type Props = { title: string; value: string };

export function CompactMetric({ title, value }: Props) {
  return (
    <Card className="rounded-2xl shadow-sm">
      <CardContent className="flex items-center justify-between px-4 py-3">
        <div className="text-sm text-neutral-500">{title}</div>
        <div className="text-lg font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}
