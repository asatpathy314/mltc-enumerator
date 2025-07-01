import { useState } from "react";
import { Attacker, Likert } from "@/lib/api";
import { getLikertLabel, formatProbability } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import EditContextItem from "./edit-context-item";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PlusCircle } from "lucide-react";

interface EditableAttackersListProps {
  attackers: Attacker[];
  onAttackersChange: (updatedAttackers: Attacker[]) => void;
}

export default function EditableAttackersList({
  attackers,
  onAttackersChange,
}: EditableAttackersListProps) {
  // Local copy for editing
  const [editingAttackers, setEditingAttackers] = useState<Attacker[]>(attackers);

  // Cache for individual edits
  const [editCache, setEditCache] = useState<Partial<Attacker>>({});
  
  if (!attackers || attackers.length === 0) {
    return (
      <div className="space-y-4">
        <Alert>
          <AlertDescription>No attackers identified.</AlertDescription>
        </Alert>
        <Button className="flex gap-2 items-center" onClick={() => handleAddAttacker()}>
          <PlusCircle size={16} /> Add Attacker
        </Button>
      </div>
    );
  }

  const handleFieldChange = (field: string, value: string | number) => {
    setEditCache({ ...editCache, [field]: value });
  };

  const handleSaveEdit = (index: number) => {
    const updatedAttackers = [...editingAttackers];
    updatedAttackers[index] = { ...updatedAttackers[index], ...editCache };
    setEditingAttackers(updatedAttackers);
    onAttackersChange(updatedAttackers);
    setEditCache({});
  };

  const handleCancelEdit = () => {
    setEditCache({});
  };

  const handleDeleteAttacker = (index: number) => {
    const updatedAttackers = [...editingAttackers];
    updatedAttackers.splice(index, 1);
    setEditingAttackers(updatedAttackers);
    onAttackersChange(updatedAttackers);
  };

  const handleAddAttacker = () => {
    const newAttacker: Attacker = {
      id: crypto.randomUUID(),
      description: "New attacker",
      skill_level: Likert.MEDIUM,
      access_level: Likert.MEDIUM,
      prob_of_attack: 0.5
    };
    const updatedAttackers = [...editingAttackers, newAttacker];
    setEditingAttackers(updatedAttackers);
    onAttackersChange(updatedAttackers);
  };

  const renderAttackerViewMode = (attacker: Attacker) => (
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
  );

  const renderAttackerEditMode = (attacker: Attacker) => (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <Label htmlFor="description">Description</Label>
        <Input
          id="description"
          value={editCache.description ?? attacker.description}
          onChange={(e) => handleFieldChange("description", e.target.value)}
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="grid gap-2">
          <Label htmlFor="skill_level">Skill Level</Label>
          <Select 
            value={String(editCache.skill_level ?? attacker.skill_level)} 
            onValueChange={(value) => handleFieldChange("skill_level", parseInt(value))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Very Low</SelectItem>
              <SelectItem value="2">Low</SelectItem>
              <SelectItem value="3">Medium</SelectItem>
              <SelectItem value="4">High</SelectItem>
              <SelectItem value="5">Very High</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="grid gap-2">
          <Label htmlFor="access_level">Access Level</Label>
          <Select 
            value={String(editCache.access_level ?? attacker.access_level)} 
            onValueChange={(value) => handleFieldChange("access_level", parseInt(value))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Very Low</SelectItem>
              <SelectItem value="2">Low</SelectItem>
              <SelectItem value="3">Medium</SelectItem>
              <SelectItem value="4">High</SelectItem>
              <SelectItem value="5">Very High</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="grid gap-2">
          <Label htmlFor="prob_of_attack">Probability of Attack (0-1)</Label>
          <Input
            id="prob_of_attack"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={editCache.prob_of_attack ?? attacker.prob_of_attack}
            onChange={(e) => handleFieldChange("prob_of_attack", parseFloat(e.target.value))}
          />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {editingAttackers.map((attacker, index) => (
        <EditContextItem
          key={attacker.id || `attacker-${index}`}
          title={attacker.description}
          onSave={() => handleSaveEdit(index)}
          onCancel={handleCancelEdit}
          onDelete={() => handleDeleteAttacker(index)}
          viewMode={renderAttackerViewMode(attacker)}
          editMode={renderAttackerEditMode(attacker)}
        />
      ))}
      
      <div className="mt-4">
        <Button className="flex gap-2 items-center" onClick={handleAddAttacker}>
          <PlusCircle size={16} /> Add Attacker
        </Button>
      </div>
    </div>
  );
} 