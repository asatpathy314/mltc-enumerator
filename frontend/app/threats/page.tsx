"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiService, ContextEnumeration, ThreatChain, EnumerateRequest } from "@/lib/api";
import { toast } from "sonner";
import { Shield, AlertTriangle, Info, Target, ChevronDown, ChevronUp } from "lucide-react";

export default function ThreatsPage() {
  const router = useRouter();
  const [contextData, setContextData] = useState<ContextEnumeration | null>(null);
  const [threatChains, setThreatChains] = useState<ThreatChain[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingStage, setLoadingStage] = useState("");
  const [expandedThreats, setExpandedThreats] = useState<Set<number>>(new Set());
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

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

  const simulateLoadingProgress = () => {
    const stages = [
      { stage: "Analyzing system context...", progress: 20 },
      { stage: "Identifying threat vectors...", progress: 40 },
      { stage: "Generating ML-specific threats...", progress: 60 },
      { stage: "Building threat chains...", progress: 80 },
      { stage: "Finalizing threat analysis...", progress: 95 },
    ];

    let currentStage = 0;
    const interval = setInterval(() => {
      if (currentStage < stages.length) {
        setLoadingStage(stages[currentStage].stage);
        setLoadingProgress(stages[currentStage].progress);
        currentStage++;
      } else {
        clearInterval(interval);
      }
    }, 1500);

    return interval;
  };

  const generateThreats = async () => {
    if (!contextData) {
      toast.error("Context data is required to generate threats");
      return;
    }

    const textualDfd = sessionStorage.getItem('contextRequest')
      ? JSON.parse(sessionStorage.getItem('contextRequest') || '{}').textual_dfd || ''
      : '';
      
    const request: EnumerateRequest = {
      ...contextData,
      textual_dfd: textualDfd,
    };

    setIsLoading(true);
    setLoadingProgress(0);
    setLoadingStage("Initializing threat analysis...");
    
    const progressInterval = simulateLoadingProgress();

    try {
      const response = await ApiService.generateThreats(request);
      setThreatChains(response.threat_chains);
      setHasGenerated(true);
      setLoadingProgress(100);
      setLoadingStage("Threat analysis complete!");
      
      clearInterval(progressInterval);
      
      toast.success(`Generated ${response.threat_chains.length} threat chains successfully!`);
    } catch (error) {
      console.error("Error generating threats:", error);
      clearInterval(progressInterval);
      toast.error("Failed to generate threat chains. Please try again.");
    } finally {
      setTimeout(() => {
        setIsLoading(false);
        setLoadingProgress(0);
        setLoadingStage("");
      }, 1000);
    }
  };

  const toggleThreatExpansion = (index: number) => {
    const newExpanded = new Set(expandedThreats);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedThreats(newExpanded);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'information_disclosure': return <Info className="w-4 h-4" />;
      case 'tampering': return <AlertTriangle className="w-4 h-4" />;
      case 'denial_of_service': return <Shield className="w-4 h-4" />;
      default: return <Target className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'information_disclosure': return 'destructive';
      case 'tampering': return 'destructive';
      case 'elevation_of_privilege': return 'destructive';
      case 'denial_of_service': return 'secondary';
      case 'spoofing': return 'secondary';
      case 'repudiation': return 'outline';
      default: return 'outline';
    }
  };

  const filteredThreats = selectedCategory === 'all' 
    ? threatChains 
    : threatChains.filter(threat => threat.category === selectedCategory);

  const threatCategories = [...new Set(threatChains.map(t => t.category))];

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
    <div className="max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Threat Enumeration</h1>
          <p className="text-muted-foreground mt-2">
            Advanced ML-aware threat modeling and chain analysis
          </p>
        </div>
        
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
            className="min-w-[160px]"
          >
            {isLoading ? "Generating..." : "Generate Threat Chains"}
          </Button>
        </div>
      </div>

      {/* Loading Progress */}
      {isLoading && (
        <Card className="mb-8">
          <CardContent className="py-6">
            <div className="space-y-4">
              <div className="text-center">
                <div className="inline-flex items-center space-x-2 mb-4">
                  <div className="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full"></div>
                  <span className="text-lg font-medium">Generating Threat Chains</span>
                </div>
                <p className="text-muted-foreground">{loadingStage}</p>
              </div>
              <Progress value={loadingProgress} className="w-full" />
              <div className="text-center text-sm text-muted-foreground">
                This process analyzes your system context to identify sophisticated threat scenarios
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Context Summary */}
      {!isLoading && contextData && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Security Context Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{contextData.attackers.length}</div>
                <div className="text-sm text-muted-foreground">Threat Actors</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{contextData.entry_points.length}</div>
                <div className="text-sm text-muted-foreground">Entry Points</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{contextData.assets.length}</div>
                <div className="text-sm text-muted-foreground">Critical Assets</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{threatChains.length}</div>
                <div className="text-sm text-muted-foreground">Threat Chains</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {hasGenerated && threatChains.length === 0 && (
        <Alert className="mb-8">
          <Info className="h-4 w-4" />
          <AlertTitle>No Threats Identified</AlertTitle>
          <AlertDescription>
            No specific threat chains were identified for this system configuration. 
            This could indicate strong security posture or may require additional context.
          </AlertDescription>
        </Alert>
      )}

      {threatChains.length > 0 && (
        <div className="space-y-6">
          {/* Threat Filters */}
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-medium">
              Identified Threat Chains ({filteredThreats.length})
            </h2>
            
            <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
              <TabsList>
                <TabsTrigger value="all">All ({threatChains.length})</TabsTrigger>
                {threatCategories.map(category => (
                  <TabsTrigger key={category} value={category}>
                    {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} ({threatChains.filter(t => t.category === category).length})
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
          </div>
          
          {/* Threat Chains */}
          <div className="space-y-6">
            {filteredThreats.map((threat, index) => {
              const isExpanded = expandedThreats.has(index);
              
              return (
                <Card key={index} className="overflow-hidden">
                  <CardHeader className="bg-slate-50 dark:bg-slate-900">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <CardTitle className="text-lg">{threat.name}</CardTitle>
                          <Badge variant={getCategoryColor(threat.category)} className="flex items-center gap-1">
                            {getCategoryIcon(threat.category)}
                            {threat.category.replace("_", " ").toUpperCase()}
                          </Badge>
                        </div>
                        <CardDescription>{threat.description}</CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleThreatExpansion(index)}
                        className="ml-4"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </Button>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="pt-6">
                    {/* Threat Chain Steps */}
                    <div className="mb-6">
                      <h3 className="text-sm font-medium text-muted-foreground mb-3">Attack Chain</h3>
                      <div className="space-y-2">
                        {threat.chain.map((step, stepIndex) => (
                          <div key={stepIndex} className="flex items-start gap-3">
                            <div className="flex-shrink-0 w-6 h-6 bg-primary rounded-full flex items-center justify-center text-white text-xs font-medium">
                              {stepIndex + 1}
                            </div>
                            <div className="flex-1 text-sm">{step}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {isExpanded && (
                      <div className="space-y-6 border-t pt-6">
                        {/* MITRE Mappings */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-2">MITRE ATT&CK</h3>
                            <p className="text-sm bg-blue-50 dark:bg-blue-950 p-3 rounded-md">
                              {threat.mitre_attack || "Not mapped"}
                            </p>
                          </div>
                          <div>
                            <h3 className="text-sm font-medium text-muted-foreground mb-2">MITRE ATLAS</h3>
                            <p className="text-sm bg-purple-50 dark:bg-purple-950 p-3 rounded-md">
                              {threat.mitre_atlas || "Not mapped"}
                            </p>
                          </div>
                        </div>
                        
                        {/* Mitigations */}
                        <div>
                          <h3 className="text-sm font-medium text-muted-foreground mb-3">Recommended Mitigations</h3>
                          <div className="grid gap-2">
                            {threat.mitigations.length > 0 ? 
                              threat.mitigations.map((mitigation, mitigationIndex) => (
                                <div key={mitigationIndex} className="flex items-start gap-2 text-sm">
                                  <Shield className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                                  <span>{mitigation}</span>
                                </div>
                              )) : 
                              <div className="text-sm text-muted-foreground italic">No specific mitigations provided</div>
                            }
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {!hasGenerated && !isLoading && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Ready to Generate Threats</CardTitle>
            <CardDescription>
              Click the "Generate Threat Chains" button to analyze the context and identify potential threat chains.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p>
                The threat generation process will identify potential attack chains connecting attackers, entry points, and assets.
                This advanced analysis includes:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
                <li>ML-specific attack vectors (model poisoning, adversarial attacks, data extraction)</li>
                <li>Traditional security threats adapted for ML systems</li>
                <li>Supply chain and dependency-related threats</li>
                <li>Data pipeline and privacy-focused attacks</li>
              </ul>
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  This process may take 1-2 minutes to complete as it performs comprehensive threat modeling.
                </AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 