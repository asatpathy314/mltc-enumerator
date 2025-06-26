import { Asset } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface AssetsListProps {
  assets: Asset[];
}

export default function AssetsList({ assets }: AssetsListProps) {
  if (!assets || assets.length === 0) {
    return (
      <Alert>
        <AlertDescription>No assets identified.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {assets.map((asset) => (
        <Card key={asset.id}>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">{asset.name}</CardTitle>
            <CardDescription>{asset.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div>
              <p className="text-sm text-muted-foreground mb-2">Failure Modes</p>
              <ul className="list-disc pl-5 space-y-1">
                {asset.failure_modes.map((mode, index) => (
                  <li key={index}>{mode}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
} 