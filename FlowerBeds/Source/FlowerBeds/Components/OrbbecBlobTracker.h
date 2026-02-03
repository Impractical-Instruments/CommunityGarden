#pragma once

#include "CoreMinimal.h"
#include "IIVision/BlobTracker.h"

#include "OrbbecBlobTracker.generated.h"

class UArrayVisualizer;
class UBlobArrayVisualizer;

struct FOrbbecFrame;
class UOrbbecCameraController;

UCLASS(ClassGroup = (FlowerBeds), meta = (BlueprintSpawnableComponent))
class UOrbbecBlobTracker : public UActorComponent
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	UArrayVisualizer* DepthFeedVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	UArrayVisualizer* BlobBgVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	UArrayVisualizer* BlobFgVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	UBlobArrayVisualizer* BlobVisualizer = nullptr;
	
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flower Beds")
	TSubclassOf<AActor> BlobActorClass;
	
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	II::Vision::FBlobTracker BlobTracker;
	
	FDelegateHandle OnFramesReceivedDelegateHandle;
	
	void OnFramesReceived(const FOrbbecFrame& ColorFrame, const FOrbbecFrame& DepthFrame, const FOrbbecFrame& IRFrame);
	
	UOrbbecCameraController* GetCameraController() const;
	
	UPROPERTY(Transient)
	TArray<TObjectPtr<AActor>> BlobActors;
	
	void UpdateWorldBlobs(const TArray<II::Vision::FBlobTracker::FBlob3D>& Blobs);
	
	void DrawBlobDebug(const FVector& WorldPos, const FVector& WorldHalfExtents) const;
};