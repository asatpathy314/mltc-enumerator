import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";

interface AssumptionsListProps {
  assumptions: string[];
}

export default function AssumptionsList({ assumptions }: AssumptionsListProps) {
  if (!assumptions || assumptions.length === 0) {
    return (
      <Alert>
        <AlertDescription>No assumptions identified.</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <ul className="list-disc pl-5 space-y-2">
          {assumptions.map((assumption, index) => (
            <li key={index}>{assumption}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
} 