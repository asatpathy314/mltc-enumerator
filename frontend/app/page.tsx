"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Shield, AlertTriangle, Loader2, CheckCircle, ArrowRight, ArrowLeft, Users, Target, FileText, RefreshCw } from "lucide-react";
import LikertScale from './components/LikertScale';
import ContextEditor from './components/ContextEditor';
import DFDInput from './components/DFDInput';
import { 
  ContextEnumeration, 
  ThreatEnumeration, 
  VerifiedContext, 
  ContextRequest, 
  AppState,
  AttackerProfileRanking,
  EntryPointRanking,
  AssetValueRanking,
  ReviewStatus,
  Likert
} from './types';
import { postContext, postGenerate } from './services/api';

export default function Home() {
  const [appState, setAppState] = useState<AppState>('input');
  const [contextEnumeration, setContextEnumeration] = useState<ContextEnumeration | null>(null);
  const [threatEnumeration, setThreatEnumeration] = useState<ThreatEnumeration | null>(null);
  const [textualDfd, setTextualDfd] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Review state
  const [reviewer, setReviewer] = useState('');
  const [attackerRankings, setAttackerRankings] = useState<Record<string, AttackerProfileRanking>>({});
  const [entryPointRankings, setEntryPointRankings] = useState<Record<string, EntryPointRanking>>({});
  const [assetRankings, setAssetRankings] = useState<Record<string, AssetValueRanking>>({});
  const [comments, setComments] = useState<Record<string, string>>({});
  const [activeReviewTab, setActiveReviewTab] = useState<'assumptions' | 'attackers' | 'entrypoints' | 'assets'>('assumptions');
  
  // Assumptions state
  const [editedAssumptions, setEditedAssumptions] = useState<string[]>([]);
  const [lastRequest, setLastRequest] = useState<ContextRequest | null>(null);

  const handleContextRequest = async (request: ContextRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await postContext(request);
      setContextEnumeration(result);
      setTextualDfd(request.textual_dfd);
      setEditedAssumptions(result.assumptions || []);
      setLastRequest(request);
      setAppState('review');
    } catch (err) {
      setError('Failed to generate context. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateThreats = async () => {
    if (!contextEnumeration || !reviewer.trim()) {
      setError('Please provide a reviewer name and ensure context is available.');
      return;
    }

    const verifiedContext: VerifiedContext = {
      textual_dfd: textualDfd,
      attackers: Object.values(attackerRankings),
      entry_points: Object.values(entryPointRankings),
      assets: Object.values(assetRankings),
      assumptions: editedAssumptions,
      questions: contextEnumeration.questions || [],
      answers: contextEnumeration.answers || [],
    };

    // Check if all items are ranked
    if (
      verifiedContext.attackers.length !== contextEnumeration.attackers.length ||
      verifiedContext.entry_points.length !== contextEnumeration.entry_points.length ||
      verifiedContext.assets.length !== contextEnumeration.assets.length
    ) {
      setError('Please rank all attackers, entry points, and assets before generating threats.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const result = await postGenerate(verifiedContext);
      setThreatEnumeration(result);
      setAppState('threats');
    } catch (err) {
      setError('Failed to generate threats. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setAppState('input');
    setContextEnumeration(null);
    setThreatEnumeration(null);
    setTextualDfd('');
    setError(null);
    setReviewer('');
    setAttackerRankings({});
    setEntryPointRankings({});
    setAssetRankings({});
    setComments({});
    setActiveReviewTab('assumptions');
    setEditedAssumptions([]);
    setLastRequest(null);
  };

  const handleAttackerRankingChange = (id: string, threat_level: Likert) => {
    setAttackerRankings((prev) => ({
      ...prev,
      [id]: { 
        attacker_id: id, 
        threat_level, 
        reviewer, 
        status: ReviewStatus.Pending, 
        comments: comments[id] || '' 
      },
    }));
  };

  const handleEntryPointRankingChange = (id: string, likelihood: Likert) => {
    setEntryPointRankings((prev) => ({
      ...prev,
      [id]: { 
        entry_id: id, 
        likelihood, 
        reviewer, 
        status: ReviewStatus.Pending, 
        comments: comments[id] || '' 
      },
    }));
  };

  const handleAssetRankingChange = (id: string, value: Likert) => {
    setAssetRankings((prev) => ({
      ...prev,
      [id]: { 
        asset_id: id, 
        value, 
        reviewer, 
        status: ReviewStatus.Pending, 
        comments: comments[id] || '' 
      },
    }));
  };
  
  const handleCommentChange = (id: string, text: string) => {
    setComments(prev => ({ ...prev, [id]: text }));
    // Update rankings with new comments
    if(attackerRankings[id]) {
        handleAttackerRankingChange(id, attackerRankings[id].threat_level);
    }
    if(entryPointRankings[id]) {
        handleEntryPointRankingChange(id, entryPointRankings[id].likelihood);
    }
    if(assetRankings[id]) {
        handleAssetRankingChange(id, assetRankings[id].value);
    }
  };

  const handleRegenerateWithAssumptions = async () => {
    if (!lastRequest) {
      setError('No previous request available for regeneration.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      // Create a new request with the original DFD and updated assumptions as extra context
      const assumptionsText = editedAssumptions.length > 0 
        ? `\n\nCORRECTED ASSUMPTIONS:\n${editedAssumptions.map((a, i) => `${i + 1}. ${a}`).join('\n')}`
        : '';
      
      const updatedRequest: ContextRequest = {
        ...lastRequest,
        extra_prompt: (lastRequest.extra_prompt || '') + assumptionsText
      };

      const result = await postContext(updatedRequest);
      setContextEnumeration(result);
      setEditedAssumptions(result.assumptions || []);
      
      // Clear existing rankings since we have new data
      setAttackerRankings({});
      setEntryPointRankings({});
      setAssetRankings({});
      setComments({});
      
    } catch (err) {
      setError('Failed to regenerate context. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderThreatDisplay = () => {
    if (!threatEnumeration) return null;

    return (
      <div className="w-full max-w-6xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-center flex items-center justify-center gap-2">
              <Shield className="h-6 w-6 text-green-600" />
              Threat Analysis Complete
            </CardTitle>
            <CardDescription className="text-center">
              {threatEnumeration.threat_chains.length} threat chain{threatEnumeration.threat_chains.length !== 1 ? 's' : ''} identified
            </CardDescription>
          </CardHeader>
        </Card>

        <div className="space-y-4">
          {threatEnumeration.threat_chains.map((threat, index) => (
            <Card key={index} className="overflow-hidden">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-500" />
                      {threat.name}
                    </CardTitle>
                    <CardDescription className="mt-2">{threat.description}</CardDescription>
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {threat.category.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-sm mb-2">Attack Chain ({threat.chain.length} steps):</h4>
                    <div className="space-y-2">
                      {threat.chain.map((step, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="bg-red-100 text-red-800 rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
                            {i + 1}
                          </div>
                          <p className="text-sm">{step}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-sm mb-2">Mitigations ({threat.mitigations.length} recommendations):</h4>
                    <div className="space-y-2">
                      {threat.mitigations.map((mitigation, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="bg-green-100 text-green-800 rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <CheckCircle className="h-3 w-3" />
                          </div>
                          <p className="text-sm">{mitigation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 pt-4 border-t">
                    <Button variant="outline" size="sm" asChild>
                      <a 
                        href={threat.mitre_atlas} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-1"
                      >
                        MITRE ATLAS
                      </a>
                    </Button>
                    <Button variant="outline" size="sm" asChild>
                      <a 
                        href={threat.mitre_attack} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-1"
                      >
                        MITRE ATT&CK
                      </a>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        
        <div className="text-center pt-6">
          <Button onClick={handleReset} variant="outline" size="lg">
            Start New Analysis
          </Button>
        </div>
      </div>
    );
  };

  const renderReviewPhase = () => {
    if (!contextEnumeration) return null;

    return (
      <div className="w-full max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-center">Review & Edit Context</CardTitle>
            <CardDescription className="text-center">
              Edit the generated context and provide your threat assessments
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Context Editor */}
        <ContextEditor 
          context={contextEnumeration} 
          onContextUpdate={setContextEnumeration} 
        />

        {/* Review Section */}
        <Card>
          <CardHeader>
            <CardTitle>Threat Assessment</CardTitle>
            <CardDescription>
              Rate each item based on your expert knowledge
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Reviewer Info */}
            <div className="space-y-2">
              <Label htmlFor="reviewer">Reviewer Name</Label>
              <Input
                id="reviewer"
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                placeholder="Enter your name"
                required
                className="max-w-xs"
              />
            </div>

            {/* Review Tab Selector */}
            <div className="flex gap-2 justify-center border-b pb-4 flex-wrap">
              <Button
                variant={activeReviewTab === 'assumptions' ? 'default' : 'outline'}
                onClick={() => setActiveReviewTab('assumptions')}
                className="flex items-center gap-2"
              >
                <FileText className="h-4 w-4" />
                Assumptions ({contextEnumeration.assumptions?.length || 0})
              </Button>
              <Button
                variant={activeReviewTab === 'attackers' ? 'default' : 'outline'}
                onClick={() => setActiveReviewTab('attackers')}
                className="flex items-center gap-2"
                disabled={contextEnumeration.attackers.length === 0}
              >
                <Users className="h-4 w-4" />
                Attackers ({contextEnumeration.attackers.length})
              </Button>
              <Button
                variant={activeReviewTab === 'entrypoints' ? 'default' : 'outline'}
                onClick={() => setActiveReviewTab('entrypoints')}
                className="flex items-center gap-2"
                disabled={contextEnumeration.entry_points.length === 0}
              >
                <Target className="h-4 w-4" />
                Entry Points ({contextEnumeration.entry_points.length})
              </Button>
              <Button
                variant={activeReviewTab === 'assets' ? 'default' : 'outline'}
                onClick={() => setActiveReviewTab('assets')}
                className="flex items-center gap-2"
                disabled={contextEnumeration.assets.length === 0}
              >
                <Shield className="h-4 w-4" />
                Assets ({contextEnumeration.assets.length})
              </Button>
            </div>

            {/* Assumptions Tab */}
            {activeReviewTab === 'assumptions' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Review & Edit Assumptions</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Review the AI's assumptions about your system. Edit them if needed and regenerate the context for better accuracy.
                </p>
                
                <div className="space-y-4">
                  {editedAssumptions.map((assumption, index) => (
                    <Card key={index} className="p-4">
                      <div className="space-y-2">
                        <Label htmlFor={`assumption-${index}`}>Assumption {index + 1}</Label>
                        <Textarea
                          id={`assumption-${index}`}
                          value={assumption}
                          onChange={(e) => {
                            const newAssumptions = [...editedAssumptions];
                            newAssumptions[index] = e.target.value;
                            setEditedAssumptions(newAssumptions);
                          }}
                          rows={2}
                        />
                      </div>
                    </Card>
                  ))}
                  
                  {editedAssumptions.length === 0 && (
                    <div className="text-center py-8">
                      <p className="text-muted-foreground">No assumptions generated yet.</p>
                    </div>
                  )}
                  
                  <div className="flex gap-2 pt-4">
                    <Button 
                      onClick={() => setEditedAssumptions([...editedAssumptions, ""])}
                      variant="outline"
                      size="sm"
                    >
                      Add Assumption
                    </Button>
                    
                    {editedAssumptions.length > 0 && (
                      <Button 
                        onClick={handleRegenerateWithAssumptions}
                        disabled={isLoading}
                        size="sm"
                      >
                                                 {isLoading ? (
                           <>
                             <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                             Regenerating...
                           </>
                         ) : (
                           <>
                             <RefreshCw className="h-4 w-4 mr-2" />
                             Regenerate with Corrected Assumptions
                           </>
                         )}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Attackers Tab */}
            {activeReviewTab === 'attackers' && contextEnumeration.attackers.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Rate Attackers</h3>
                <div className="space-y-4">
                  {contextEnumeration.attackers.map((attacker) => (
                    <Card key={attacker.id} className="p-4">
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium">{attacker.description}</h4>
                          <p className="text-sm text-muted-foreground">
                            Skill: {Likert[attacker.skill_level]} | Access: {Likert[attacker.access_level]} | Prob: {attacker.prob_of_attack}
                          </p>
                        </div>
                        <LikertScale
                          title="Threat Level"
                          value={attackerRankings[attacker.id]?.threat_level || Likert.Medium}
                          onChange={(val) => handleAttackerRankingChange(attacker.id, val)}
                        />
                        <Textarea
                          placeholder="Comments..."
                          value={comments[attacker.id] || ''}
                          onChange={(e) => handleCommentChange(attacker.id, e.target.value)}
                        />
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Entry Points Tab */}
            {activeReviewTab === 'entrypoints' && contextEnumeration.entry_points.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Rate Entry Points</h3>
                <div className="space-y-4">
                  {contextEnumeration.entry_points.map((entry) => (
                    <Card key={entry.id} className="p-4">
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium">{entry.name}</h4>
                          <p className="text-sm text-muted-foreground">{entry.description}</p>
                          <p className="text-sm text-muted-foreground">
                            Difficulty: {Likert[entry.difficulty_of_entry]} | Prob: {entry.prob_of_entry}
                          </p>
                        </div>
                        <LikertScale
                          title="Likelihood"
                          value={entryPointRankings[entry.id]?.likelihood || Likert.Medium}
                          onChange={(val) => handleEntryPointRankingChange(entry.id, val)}
                        />
                        <Textarea
                          placeholder="Comments..."
                          value={comments[entry.id] || ''}
                          onChange={(e) => handleCommentChange(entry.id, e.target.value)}
                        />
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Assets Tab */}
            {activeReviewTab === 'assets' && contextEnumeration.assets.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Rate Assets</h3>
                <div className="space-y-4">
                  {contextEnumeration.assets.map((asset) => (
                    <Card key={asset.id} className="p-4">
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium">{asset.name}</h4>
                          <p className="text-sm text-muted-foreground">{asset.description}</p>
                          <p className="text-sm text-muted-foreground">
                            Failure Modes: {asset.failure_modes.join(', ')}
                          </p>
                        </div>
                        <LikertScale
                          title="Value"
                          value={assetRankings[asset.id]?.value || Likert.Medium}
                          onChange={(val) => handleAssetRankingChange(asset.id, val)}
                        />
                        <Textarea
                          placeholder="Comments..."
                          value={comments[asset.id] || ''}
                          onChange={(e) => handleCommentChange(asset.id, e.target.value)}
                        />
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state for active tab */}
            {((activeReviewTab === 'attackers' && contextEnumeration.attackers.length === 0) ||
              (activeReviewTab === 'entrypoints' && contextEnumeration.entry_points.length === 0) ||
              (activeReviewTab === 'assets' && contextEnumeration.assets.length === 0)) && (
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  No {activeReviewTab === 'attackers' ? 'attackers' : activeReviewTab === 'entrypoints' ? 'entry points' : 'assets'} to review yet.
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Use the editor above to add some items first.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-between pt-6">
          <Button variant="outline" onClick={handleReset}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Start Over
          </Button>
          <Button 
            onClick={handleGenerateThreats}
            disabled={!reviewer.trim() || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                Generate Threats
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <Card className="border-none shadow-lg bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Shield className="h-10 w-10 text-blue-600 dark:text-blue-400" />
              <CardTitle className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                MLTC Enumerator
              </CardTitle>
            </div>
            <CardDescription className="text-lg text-muted-foreground max-w-2xl mx-auto">
              A comprehensive tool for enumerating threats in Machine Learning systems. 
              Analyze your ML infrastructure, identify potential attack vectors, and get actionable security recommendations.
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
            <CardContent className="flex items-center gap-2 pt-6">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <p className="text-red-800 dark:text-red-200 font-medium">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Loading State */}
        {isLoading && appState === 'input' && (
          <Card className="max-w-4xl mx-auto">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">
                Analyzing your system and generating context...
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                This may take a moment
              </p>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        {!isLoading && (
          <div className="space-y-8">
            {appState === 'input' && (
              <DFDInput onSubmit={handleContextRequest} isLoading={isLoading} />
            )}
            {appState === 'review' && renderReviewPhase()}
            {appState === 'threats' && renderThreatDisplay()}
          </div>
        )}
      </div>
    </main>
  );
}
