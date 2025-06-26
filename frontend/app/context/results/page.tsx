"use client";

import { useEffect, useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ApiService, ContextEnumeration, Likert, ContextRegenerationRequest, Attacker, EntryPoint, Asset } from '@/lib/api';
import AttackersList from '@/components/attackers-list';
import EntryPointsList from '@/components/entry-points-list';
import AssetsList from '@/components/assets-list';
import AssumptionsList from '@/components/assumptions-list';
import { toast } from 'sonner';

export default function ContextResultsPage() {
  const router = useRouter();
  const [contextData, setContextData] = useState<ContextEnumeration | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    const storedData = sessionStorage.getItem('contextEnumeration');
    if (storedData) {
      setContextData(JSON.parse(storedData));
    } else {
      toast.error('No context data found. Please submit a new request.');
      router.push('/context');
    }
  }, [router]);

  const handleRegenerate = async () => {
    if (!contextData) {
      toast.error('No context data to regenerate.');
      return;
    }

    // Build the ContextRegenerationRequest from the current contextData
    const regenRequest: ContextRegenerationRequest = {
      textual_dfd: sessionStorage.getItem('contextRequest')
        ? JSON.parse(sessionStorage.getItem('contextRequest') || '{}').textual_dfd || ''
        : '',
      attackers: contextData.attackers as Attacker[],
      entry_points: contextData.entry_points as EntryPoint[],
      assets: contextData.assets as Asset[],
      assumptions: contextData.assumptions,
      questions: contextData.questions,
      answers: contextData.answers,
    };

    startTransition(async () => {
      try {
        const regeneratedData = await ApiService.regenerateContext(regenRequest);
        setContextData(regeneratedData);
        sessionStorage.setItem('contextEnumeration', JSON.stringify(regeneratedData));
        toast.success('Context has been regenerated!');
      } catch (error) {
        toast.error('Failed to regenerate context. Please try again.');
        console.error(error);
      }
    });
  };

  if (!contextData) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite] mr-2"></div>
        <span>Loading context data...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Context Results</h1>
        <div className="flex items-center gap-4">
          <Button onClick={handleRegenerate} disabled={isPending}>
            {isPending ? 'Regenerating...' : 'Regenerate'}
          </Button>
          <Button variant="outline" onClick={() => router.push('/threats')}>
            View Threat Model
          </Button>
        </div>
      </div>

      <Tabs defaultValue="attackers">
        <TabsList className="mb-8 w-full grid grid-cols-4">
          <TabsTrigger value="attackers">Attackers</TabsTrigger>
          <TabsTrigger value="entry-points">Entry Points</TabsTrigger>
          <TabsTrigger value="assets">Assets</TabsTrigger>
          <TabsTrigger value="assumptions">Assumptions</TabsTrigger>
        </TabsList>
        <TabsContent value="attackers">
          <h2 className="text-xl font-semibold mb-4">Identified Attackers</h2>
          <AttackersList attackers={contextData.attackers} />
        </TabsContent>
        <TabsContent value="entry-points">
          <h2 className="text-xl font-semibold mb-4">Identified Entry Points</h2>
          <EntryPointsList entryPoints={contextData.entry_points} />
        </TabsContent>
        <TabsContent value="assets">
          <h2 className="text-xl font-semibold mb-4">Identified Assets</h2>
          <AssetsList assets={contextData.assets} />
        </TabsContent>
        <TabsContent value="assumptions">
          <h2 className="text-xl font-semibold mb-4">Key Assumptions</h2>
          <AssumptionsList assumptions={contextData.assumptions} />
        </TabsContent>
      </Tabs>
    </div>
  );
} 