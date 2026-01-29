#pragma once

#include "CoreMinimal.h"

#include "BlobTrackerVisualizer.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBlobTrackerBgDepthTextureUpdated, UTexture2D*, Texture);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBlobTrackerForegroundTextureUpdated, UTexture2D*, Texture);

UCLASS(BlueprintType)
class IIVISION_API UBlobTrackerVisualizer : public UObject
{
	GENERATED_BODY()
	
public:
	UPROPERTY(Transient, BlueprintReadOnly)
	UTexture2D* BackgroundDepthTexture = nullptr;
	
	UPROPERTY(BlueprintAssignable)
	FBlobTrackerBgDepthTextureUpdated OnBackgroundDepthTextureUpdated;
	
	void SetBackgroundDepthMap(const TArray<uint16>& DepthMap, int32 Width, int32 Height);
	
	UPROPERTY(Transient, BlueprintReadOnly)
	UTexture2D* ForegroundMaskTexture = nullptr;
	
	UPROPERTY(BlueprintAssignable)
	FBlobTrackerForegroundTextureUpdated OnForegroundTextureUpdated;
	
	void SetForegroundMask(const TArray<uint8>& Mask, int32 Width, int32 Height);
};