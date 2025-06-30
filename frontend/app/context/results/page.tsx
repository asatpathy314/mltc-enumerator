"use client";

import { useEffect, useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ApiService, ContextEnumeration, ContextRegenerationRequest, Attacker, EntryPoint, Asset } from '@/lib/api';
import { deepClone } from '@/lib/utils';
import EditableAttackersList from '@/components/editable-attackers-list';
import EditableEntryPointsList from '@/components/editable-entry-points-list';
import EditableAssetsList from '@/components/editable-assets-list';
import EditableAssumptionsList from '@/components/editable-assumptions-list';
import { toast } from 'sonner';

export default function ContextResultsPage() {
  const router = useRouter();
  const [contextData, setContextData] = useState<ContextEnumeration | null>(null);
  const [editedContext, setEditedContext] = useState<ContextEnumeration | null>(null);
  const [isPending, startTransition] = useTransition();
  const [hasEdits, setHasEdits] = useState(false);

  useEffect(() => {
    const storedData = sessionStorage.getItem('contextEnumeration');
    if (storedData) {
      const parsedData = JSON.parse(storedData);
      setContextData(parsedData);
      setEditedContext(deepClone(parsedData));
    } else {
      toast.error('No context data found. Please submit a new request.');
      router.push('/context');
    }
  }, [router]);

  const handleAttackersChange = (updatedAttackers: Attacker[]) => {
    if (!editedContext) return;
    
    const updatedContext = {
      ...editedContext,
      attackers: updatedAttackers
    };
    
    setEditedContext(updatedContext);
    setHasEdits(true);
  };

  const handleEntryPointsChange = (updatedEntryPoints: EntryPoint[]) => {
    if (!editedContext) return;
    
    const updatedContext = {
      ...editedContext,
      entry_points: updatedEntryPoints
    };
    
    setEditedContext(updatedContext);
    setHasEdits(true);
  };

  const handleAssetsChange = (updatedAssets: Asset[]) => {
    if (!editedContext) return;
    
    const updatedContext = {
      ...editedContext,
      assets: updatedAssets
    };
    
    setEditedContext(updatedContext);
    setHasEdits(true);
  };

  const handleAssumptionsChange = (updatedAssumptions: string[]) => {
    if (!editedContext) return;
    
    const updatedContext = {
      ...editedContext,
      assumptions: updatedAssumptions
    };
    
    setEditedContext(updatedContext);
    setHasEdits(true);
  };

  const handleRegenerate = async () => {
    if (!editedContext) {
      toast.error('No context data to regenerate.');
      return;
    }

    // Build the ContextRegenerationRequest from the edited context data
    const regenRequest: ContextRegenerationRequest = {
      textual_dfd: sessionStorage.getItem('contextRequest')
        ? JSON.parse(sessionStorage.getItem('contextRequest') || '{}').textual_dfd || ''
        : '',
      attackers: editedContext.attackers,
      entry_points: editedContext.entry_points,
      assets: editedContext.assets,
      assumptions: editedContext.assumptions,
      questions: editedContext.questions,
      answers: editedContext.answers,
    };

    startTransition(async () => {
      try {
        const regeneratedData = await ApiService.regenerateContext(regenRequest);
        setContextData(regeneratedData);
        setEditedContext(deepClone(regeneratedData));
        sessionStorage.setItem('contextEnumeration', JSON.stringify(regeneratedData));
        toast.success('Context has been regenerated with your edits!');
        setHasEdits(false);
      } catch (error) {
        toast.error('Failed to regenerate context. Please try again.');
        console.error(error);
      }
    });
  };

  const handleSaveChanges = () => {
    if (!editedContext) return;
    
    // Update the context data with edited values
    setContextData(deepClone(editedContext));
    sessionStorage.setItem('contextEnumeration', JSON.stringify(editedContext));
    toast.success('Changes have been saved!');
    setHasEdits(false);
  };

  if (!contextData || !editedContext) {
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
          {hasEdits && (
            <Button onClick={handleSaveChanges} variant="secondary">
              Save Changes
            </Button>
          )}
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
          <EditableAttackersList 
            attackers={editedContext.attackers} 
            onAttackersChange={handleAttackersChange}
          />
        </TabsContent>
        <TabsContent value="entry-points">
          <h2 className="text-xl font-semibold mb-4">Identified Entry Points</h2>
          <EditableEntryPointsList 
            entryPoints={editedContext.entry_points} 
            onEntryPointsChange={handleEntryPointsChange}
          />
        </TabsContent>
        <TabsContent value="assets">
          <h2 className="text-xl font-semibold mb-4">Identified Assets</h2>
          <EditableAssetsList 
            assets={editedContext.assets} 
            onAssetsChange={handleAssetsChange}
          />
        </TabsContent>
        <TabsContent value="assumptions">
          <h2 className="text-xl font-semibold mb-4">Key Assumptions</h2>
          <EditableAssumptionsList 
            assumptions={editedContext.assumptions} 
            onAssumptionsChange={handleAssumptionsChange}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
} 