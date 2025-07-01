import { useState } from "react";
import { EntryPoint, Likert } from "@/lib/api";
import { getLikertLabel, formatProbability } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import EditContextItem from "./edit-context-item";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PlusCircle } from "lucide-react";

interface EditableEntryPointsListProps {
  entryPoints: EntryPoint[];
  onEntryPointsChange: (updatedEntryPoints: EntryPoint[]) => void;
}

export default function EditableEntryPointsList({
  entryPoints,
  onEntryPointsChange,
}: EditableEntryPointsListProps) {
  // Local copy for editing
  const [editingEntryPoints, setEditingEntryPoints] = useState<EntryPoint[]>(entryPoints);

  // Cache for individual edits
  const [editCache, setEditCache] = useState<Partial<EntryPoint>>({});
  
  if (!entryPoints || entryPoints.length === 0) {
    return (
      <div className="space-y-4">
        <Alert>
          <AlertDescription>No entry points identified.</AlertDescription>
        </Alert>
        <Button className="flex gap-2 items-center" onClick={() => handleAddEntryPoint()}>
          <PlusCircle size={16} /> Add Entry Point
        </Button>
      </div>
    );
  }

  const handleFieldChange = (field: string, value: string | number) => {
    setEditCache({ ...editCache, [field]: value });
  };

  const handleSaveEdit = (index: number) => {
    const updatedEntryPoints = [...editingEntryPoints];
    updatedEntryPoints[index] = { ...updatedEntryPoints[index], ...editCache };
    setEditingEntryPoints(updatedEntryPoints);
    onEntryPointsChange(updatedEntryPoints);
    setEditCache({});
  };

  const handleCancelEdit = () => {
    setEditCache({});
  };

  const handleDeleteEntryPoint = (index: number) => {
    const updatedEntryPoints = [...editingEntryPoints];
    updatedEntryPoints.splice(index, 1);
    setEditingEntryPoints(updatedEntryPoints);
    onEntryPointsChange(updatedEntryPoints);
  };

  const handleAddEntryPoint = () => {
    const newEntryPoint: EntryPoint = {
      id: crypto.randomUUID(),
      name: "New Entry Point",
      description: "Description of entry point",
      prob_of_entry: 0.5,
      difficulty_of_entry: Likert.MEDIUM
    };
    const updatedEntryPoints = [...editingEntryPoints, newEntryPoint];
    setEditingEntryPoints(updatedEntryPoints);
    onEntryPointsChange(updatedEntryPoints);
  };

  const renderEntryPointViewMode = (entryPoint: EntryPoint) => (
    <div>
      <div className="mb-4">
        <p className="text-muted-foreground mb-1">Description</p>
        <p>{entryPoint.description}</p>
      </div>
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
    </div>
  );

  const renderEntryPointEditMode = (entryPoint: EntryPoint) => (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={editCache.name ?? entryPoint.name}
          onChange={(e) => handleFieldChange("name", e.target.value)}
        />
      </div>

      <div className="grid gap-2">
        <Label htmlFor="description">Description</Label>
        <Input
          id="description"
          value={editCache.description ?? entryPoint.description}
          onChange={(e) => handleFieldChange("description", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label htmlFor="prob_of_entry">Probability of Entry (0-1)</Label>
          <Input
            id="prob_of_entry"
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={editCache.prob_of_entry ?? entryPoint.prob_of_entry}
            onChange={(e) => handleFieldChange("prob_of_entry", parseFloat(e.target.value))}
          />
        </div>
        
        <div className="grid gap-2">
          <Label htmlFor="difficulty_of_entry">Difficulty of Entry</Label>
          <Select 
            value={String(editCache.difficulty_of_entry ?? entryPoint.difficulty_of_entry)} 
            onValueChange={(value) => handleFieldChange("difficulty_of_entry", parseInt(value))}
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
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {editingEntryPoints.map((entryPoint, index) => (
        <EditContextItem
          key={entryPoint.id || `entry-point-${index}`}
          title={entryPoint.name}
          description={entryPoint.description}
          onSave={() => handleSaveEdit(index)}
          onCancel={handleCancelEdit}
          onDelete={() => handleDeleteEntryPoint(index)}
          viewMode={renderEntryPointViewMode(entryPoint)}
          editMode={renderEntryPointEditMode(entryPoint)}
        />
      ))}
      
      <div className="mt-4">
        <Button className="flex gap-2 items-center" onClick={handleAddEntryPoint}>
          <PlusCircle size={16} /> Add Entry Point
        </Button>
      </div>
    </div>
  );
} 