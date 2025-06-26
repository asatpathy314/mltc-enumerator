"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ContextEnumeration, Likert, ReviewStatus, AttackerProfileRanking, EntryPointRanking, AssetValueRanking } from '@/lib/api';
import AttackersList from '@/components/attackers-list';
import EntryPointsList from '@/components/entry-points-list';
import AssetsList from '@/components/assets-list';
import AssumptionsList from '@/components/assumptions-list';
import { toast } from 'sonner';

export default function ContextResultsPage() {
  const router = useRouter();
  const [contextData, setContextData] = useState<ContextEnumeration | null>(null);
  const [verificationComplete, setVerificationComplete] = useState(false);
  const [reviewer, setReviewer] = useState<string>('');

  useEffect(() => {
    // Load context data from session storage
    const storedData = sessionStorage.getItem('contextEnumeration');
    
    if (storedData) {
      try {
        const parsedData = JSON.parse(storedData);
        setContextData(parsedData);
      } catch (error) {
        console.error('Error parsing context data:', error);
        toast.error('Failed to load context data. Please try again.');
        router.push('/context');
      }
    } else {
      // No data found, redirect to context page
      toast.error('No context data found. Please submit a new request.');
      router.push('/context');
    }
  }, [router]);

  const handleVerify = () => {
    if (!contextData || !reviewer) {
      toast.error('Please enter a reviewer name before continuing');
      return;
    }

    // Transform context data into verified context
    const attackerRankings: AttackerProfileRanking[] = contextData.attackers.map(attacker => ({
      attacker_id: attacker.id,
      threat_level: Likert.MEDIUM, // Default value
      reviewer: reviewer,
      status: ReviewStatus.ACCEPTED
    }));

    const entryPointRankings: EntryPointRanking[] = contextData.entry_points.map(entry => ({
      entry_id: entry.id,
      likelihood: Likert.MEDIUM, // Default value
      reviewer: reviewer,
      status: ReviewStatus.ACCEPTED
    }));

    const assetRankings: AssetValueRanking[] = contextData.assets.map(asset => ({
      asset_id: asset.id,
      value: Likert.MEDIUM, // Default value
      reviewer: reviewer,
      status: ReviewStatus.ACCEPTED
    }));

    // Store verified context data for threats page
    const textual_dfd = sessionStorage.getItem('contextRequest') 
      ? JSON.parse(sessionStorage.getItem('contextRequest') || '{}').textual_dfd || ''
      : '';

    sessionStorage.setItem('verifiedContext', JSON.stringify({
      textual_dfd: textual_dfd,
      attackers: attackerRankings,
      entry_points: entryPointRankings,
      assets: assetRankings,
      assumptions: contextData.assumptions,
      questions: contextData.questions,
      answers: contextData.answers,
    }));

    setVerificationComplete(true);
    toast.success('Context verification completed!');
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
          {!verificationComplete ? (
            <>
              <input
                type="text"
                placeholder="Reviewer name"
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                className="px-3 py-2 border rounded-md"
              />
              <Button onClick={handleVerify} disabled={!reviewer}>
                Verify Context
              </Button>
            </>
          ) : (
            <div className="flex gap-4">
              <Button variant="outline" onClick={() => router.push('/threats')}>
                View Threat Model
              </Button>
              <Button onClick={() => router.push('/context')}>
                New Analysis
              </Button>
            </div>
          )}
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