#pragma once

#include "CoreMinimal.h"

#include "ArrayVisualizer.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FArrayVisualizerTextureInitialized, UTexture2D*, Texture);

UCLASS(BlueprintType)
class UArrayVisualizer : public UObject
{
	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadOnly) 
	UTexture2D* Texture = nullptr;
	
	UPROPERTY(BlueprintAssignable) 
	FArrayVisualizerTextureInitialized OnInitialized;

	void InitTexture(int32 Width, int32 Height, EPixelFormat PF, bool bSRGB);

	void UpdateTexture(const uint8* Data, int32 Width, int32 Height, EPixelFormat PF);
};
