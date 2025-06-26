import { EntryPoint } from "@/lib/api";
import { getLikertLabel, formatProbability } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface EntryPointsListProps {
  entryPoints: EntryPoint[];
}

export default function EntryPointsList({ entryPoints }: EntryPointsListProps) {
  if (!entryPoints || entryPoints.length === 0) {
    return (
      <Alert>
        <AlertDescription>No entry points identified.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {entryPoints.map((entryPoint) => (
        <Card key={entryPoint.id}>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">{entryPoint.name}</CardTitle>
            <CardDescription>{entryPoint.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Probability of Entry</p>
                <p className="font-medium">{formatProbability(entryPoint.prob_of_entry)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Difficulty of Entry</p>
                <p className="font-medium">{getLikertLabel(entryPoint.difficulty_of_entry)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
} 