"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiService, ContextEnumeration, ThreatChain, ContextRegenerationRequest } from "@/lib/api";
import { toast } from "sonner";

export default function ThreatsPage() {
  const router = useRouter();
  const [contextData, setContextData] = useState<ContextEnumeration | null>(null);
  const [threatChains, setThreatChains] = useState<ThreatChain[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);

  useEffect(() => {
    // Load context data from session storage
    const storedContext = sessionStorage.getItem('contextEnumeration');
    
    if (storedContext) {
      try {
        const parsedContext = JSON.parse(storedContext);
        setContextData(parsedContext);
      } catch (error) {
        console.error('Error parsing context data:', error);
        toast.error('Failed to load context data. Please go back and create context first.');
        router.push('/context');
      }
    } else {
      // No data found, redirect to context page
      toast.error('No context data found. Please submit context first.');
      setTimeout(() => router.push('/context'), 2000);
    }
  }, [router]);

  const generateThreats = async () => {
    if (!contextData) {
      toast.error("Context data is required to generate threats");
      return;
    }

    const textualDfd = sessionStorage.getItem('contextRequest')
      ? JSON.parse(sessionStorage.getItem('contextRequest') || '{}').textual_dfd || ''
      : '';
      
    const request: ContextRegenerationRequest = {
      textual_dfd: textualDfd,
      attackers: contextData.attackers,
      entry_points: contextData.entry_points,
      assets: contextData.assets,
      assumptions: contextData.assumptions,
      questions: contextData.questions,
      answers: contextData.answers,
    };

    setIsLoading(true);
    try {
      const response = await ApiService.generateThreats(request);
      setThreatChains(response.threat_chains);
      setHasGenerated(true);
      toast.success("Threat chains generated successfully!");
    } catch (error) {
      console.error("Error generating threats:", error);
      toast.error("Failed to generate threat chains. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!contextData) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite] mr-2"></div>
          <span>Loading context data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Threat Enumeration</h1>
        
        <div className="flex items-center gap-4">
          <Button 
            onClick={() => router.push('/context/results')}
            variant="outline"
          >
            Back to Context
          </Button>
          
          <Button 
            onClick={generateThreats}
            disabled={isLoading}
          >
            {isLoading ? "Generating..." : "Generate Threat Chains"}
          </Button>
        </div>
      </div>

      {hasGenerated && threatChains.length === 0 && (
        <Card className="mb-8">
          <CardContent className="py-6">
            <div className="text-center text-muted-foreground">
              <p>No threat chains were identified.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {threatChains.length > 0 && (
        <div className="space-y-8">
          <h2 className="text-xl font-medium">Identified Threat Chains ({threatChains.length})</h2>
          
          {threatChains.map((threat, index) => (
            <Card key={index} className="overflow-hidden">
              <CardHeader className="bg-slate-50 dark:bg-slate-900">
                <CardTitle>{threat.name}</CardTitle>
                <CardDescription className="capitalize">Category: {threat.category.replace("_", " ")}</CardDescription>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Threat Chain</h3>
                  <ol className="list-decimal list-inside space-y-1 pl-4">
                    {threat.chain.map((step, stepIndex) => (
                      <li key={stepIndex}>{step}</li>
                    ))}
                  </ol>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Description</h3>
                  <p>{threat.description}</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">MITRE ATT&CK</h3>
                    <p>{threat.mitre_attack || "N/A"}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">MITRE ATLAS</h3>
                    <p>{threat.mitre_atlas || "N/A"}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Mitigations</h3>
                  <ul className="list-disc list-inside space-y-1 pl-4">
                    {threat.mitigations.length > 0 ? 
                      threat.mitigations.map((mitigation, mitigationIndex) => (
                        <li key={mitigationIndex}>{mitigation}</li>
                      )) : 
                      <li>No mitigations provided</li>
                    }
                  </ul>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!hasGenerated && !isLoading && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Ready to Generate Threats</CardTitle>
            <CardDescription>
              Click the &quot;Generate Threat Chains&quot; button to analyze the context and identify potential threat chains.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p>
              The threat generation process will identify potential attack chains connecting attackers, entry points, and assets.
              This may take up to a minute to complete.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 