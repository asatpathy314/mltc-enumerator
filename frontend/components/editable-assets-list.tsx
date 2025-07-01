import { useState } from "react";
import { Asset } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import EditContextItem from "./edit-context-item";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PlusCircle, X } from "lucide-react";

interface EditableAssetsListProps {
  assets: Asset[];
  onAssetsChange: (updatedAssets: Asset[]) => void;
}

export default function EditableAssetsList({
  assets,
  onAssetsChange,
}: EditableAssetsListProps) {
  // Local copy for editing
  const [editingAssets, setEditingAssets] = useState<Asset[]>(assets);

  // Cache for individual edits
  const [editCache, setEditCache] = useState<Partial<Asset & { tempFailureModes?: string[] }>>({});
  
  if (!assets || assets.length === 0) {
    return (
      <div className="space-y-4">
        <Alert>
          <AlertDescription>No assets identified.</AlertDescription>
        </Alert>
        <Button className="flex gap-2 items-center" onClick={() => handleAddAsset()}>
          <PlusCircle size={16} /> Add Asset
        </Button>
      </div>
    );
  }

  const handleFieldChange = (field: string, value: string | number | string[]) => {
    setEditCache({ ...editCache, [field]: value });
  };

  const handleFailureModeChange = (index: number, value: string) => {
    const updatedModes = [...(editCache.tempFailureModes || [])];
    updatedModes[index] = value;
    setEditCache({ ...editCache, tempFailureModes: updatedModes });
  };

  const handleAddFailureMode = () => {
    const updatedModes = [...(editCache.tempFailureModes || []), "New failure mode"];
    setEditCache({ ...editCache, tempFailureModes: updatedModes });
  };

  const handleRemoveFailureMode = (index: number) => {
    const updatedModes = [...(editCache.tempFailureModes || [])];
    updatedModes.splice(index, 1);
    setEditCache({ ...editCache, tempFailureModes: updatedModes });
  };

  const handleSaveEdit = (index: number) => {
    const updatedAssets = [...editingAssets];
    const finalAsset = {
      ...updatedAssets[index],
      ...editCache,
      failure_modes: editCache.tempFailureModes || updatedAssets[index].failure_modes
    };
    
    // Remove the temp property
    const cleanAsset = { ...finalAsset };
    delete cleanAsset.tempFailureModes;
    
    updatedAssets[index] = cleanAsset as Asset;
    setEditingAssets(updatedAssets);
    onAssetsChange(updatedAssets);
    setEditCache({});
  };

  const handleCancelEdit = () => {
    setEditCache({});
  };

  const handleDeleteAsset = (index: number) => {
    const updatedAssets = [...editingAssets];
    updatedAssets.splice(index, 1);
    setEditingAssets(updatedAssets);
    onAssetsChange(updatedAssets);
  };

  const handleAddAsset = () => {
    const newAsset: Asset = {
      id: crypto.randomUUID(),
      name: "New Asset",
      description: "Description of asset",
      failure_modes: ["Failure mode 1", "Failure mode 2"]
    };
    const updatedAssets = [...editingAssets, newAsset];
    setEditingAssets(updatedAssets);
    onAssetsChange(updatedAssets);
  };

  const renderAssetViewMode = (asset: Asset) => (
    <div>
      <div className="mb-4">
        <p className="text-muted-foreground mb-1">Description</p>
        <p>{asset.description}</p>
      </div>
      <div>
        <p className="text-sm text-muted-foreground mb-2">Failure Modes</p>
        <ul className="list-disc pl-5 space-y-1">
          {asset.failure_modes.map((mode, index) => (
            <li key={index}>{mode}</li>
          ))}
        </ul>
      </div>
    </div>
  );

  const renderAssetEditMode = (asset: Asset) => (
    <div className="grid gap-4">
      <div className="grid gap-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={editCache.name ?? asset.name}
          onChange={(e) => handleFieldChange("name", e.target.value)}
        />
      </div>

      <div className="grid gap-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={editCache.description ?? asset.description}
          onChange={(e) => handleFieldChange("description", e.target.value)}
        />
      </div>

      <div className="grid gap-2">
        <div className="flex items-center justify-between">
          <Label>Failure Modes</Label>
          <Button 
            type="button" 
            variant="outline" 
            size="sm"
            onClick={handleAddFailureMode}
            className="flex items-center gap-1"
          >
            <PlusCircle size={16} />
            Add
          </Button>
        </div>
        
        <div className="space-y-2">
          {(editCache.tempFailureModes || asset.failure_modes).map((mode, index) => (
            <div key={index} className="flex gap-2">
              <Input
                value={mode}
                onChange={(e) => handleFailureModeChange(index, e.target.value)}
                placeholder={`Failure mode ${index + 1}`}
              />
              <Button 
                type="button" 
                variant="ghost" 
                size="icon"
                onClick={() => handleRemoveFailureMode(index)}
              >
                <X size={16} />
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {editingAssets.map((asset, index) => (
        <EditContextItem
          key={asset.id || `asset-${index}`}
          title={asset.name}
          description={asset.description}
          onSave={() => handleSaveEdit(index)}
          onCancel={handleCancelEdit}
          onDelete={() => handleDeleteAsset(index)}
          viewMode={renderAssetViewMode(asset)}
          editMode={renderAssetEditMode(asset)}
        />
      ))}
      
      <div className="mt-4">
        <Button className="flex gap-2 items-center" onClick={handleAddAsset}>
          <PlusCircle size={16} /> Add Asset
        </Button>
      </div>
    </div>
  );
} 