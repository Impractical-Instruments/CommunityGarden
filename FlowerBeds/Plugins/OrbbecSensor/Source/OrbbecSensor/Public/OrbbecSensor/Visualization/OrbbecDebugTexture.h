#pragma once

#include "CoreMinimal.h"

#include "OrbbecDebugTexture.generated.h"

struct FOrbbecFrame;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOrbbecDebugTextureInitialized, UTexture2D*, Texture);

UCLASS(BlueprintType)
class UOrbbecDebugTexture : public UObject
{
	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadOnly) 
	UTexture2D* Texture = nullptr;
	
	UPROPERTY(BlueprintAssignable) 
	FOrbbecDebugTextureInitialized OnInitialized;
	
	UFUNCTION(BlueprintCallable) 
	void UpdateTexture(const FOrbbecFrame& Frame);

private:
	void EnsureTexture(int32 W, int32 H, EPixelFormat PF, bool bSRGB);
	static void UpdateTexture(UTexture2D* Tex, int32 W, int32 H, const TArray<uint8>& Data, int32 SrcStride, int32 TargetStride);
};
