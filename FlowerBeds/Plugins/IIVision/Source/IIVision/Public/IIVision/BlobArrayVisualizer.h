#pragma once

#include "CoreMinimal.h"
#include "BlobTracker.h"

#include "BlobArrayVisualizer.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBlobArrayVisualizerTextureInitialized, UTexture2D*, Texture);

UCLASS(BlueprintType)
class IIVISION_API UBlobArrayVisualizer : public UObject
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly) 
	UTexture2D* Texture = nullptr;
	
	UPROPERTY(BlueprintAssignable) 
	FBlobArrayVisualizerTextureInitialized OnInitialized;

	void InitTexture(int32 InWidth, int32 InHeight);
	
	void UpdateTexture(const TArray<II::Vision::FBlobTracker::FBlob2D>& Blobs);
	
private:
	TArray<FColor> Data;
	TUniquePtr<FUpdateTextureRegion2D> UpdateRegion;
	int32 Width, Height;
	
	void PutPixel(int32 X, int32 Y, const FColor& Color);
	void DrawBlobRect(const II::Vision::FBlobTracker::FBlob2D& Blob, const FColor& Color);
};
