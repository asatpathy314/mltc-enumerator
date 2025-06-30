import { Attacker } from "@/lib/api";
import { getLikertLabel, formatProbability } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface AttackersListProps {
  attackers: Attacker[];
}

export default function AttackersList({ attackers }: AttackersListProps) {
  if (!attackers || attackers.length === 0) {
    return (
      <Alert>
        <AlertDescription>No attackers identified.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {attackers.map((attacker, index) => (
        <Card key={attacker.id || `${attacker.description}-${index}`}>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">{attacker.description}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Skill Level</p>
                <p className="font-medium">{getLikertLabel(attacker.skill_level)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Access Level</p>
                <p className="font-medium">{getLikertLabel(attacker.access_level)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Attack Probability</p>
                <p className="font-medium">{formatProbability(attacker.prob_of_attack)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
} 