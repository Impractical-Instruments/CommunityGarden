#pragma once

#include "CoreMinimal.h"
#include "IIVision/BlobTracker.h"

#include "OrbbecBlobTracker.generated.h"

struct FOrbbecFrame;
class UOrbbecCameraController;

UCLASS(ClassGroup = (FlowerBeds), meta = (BlueprintSpawnableComponent))
class UOrbbecBlobTracker : public UActorComponent
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	UOrbbecCameraController* CameraController;
	
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	II::Vision::FBlobTracker BlobTracker;
	
	FDelegateHandle OnFramesReceivedDelegateHandle;
	
	void OnFramesReceived(const FOrbbecFrame& ColorFrame, const FOrbbecFrame& DepthFrame, const FOrbbecFrame& IRFrame);
};