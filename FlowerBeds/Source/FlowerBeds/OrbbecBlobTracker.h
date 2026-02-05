#pragma once

#include "CoreMinimal.h"
#include "IIVision/BlobTracker.h"

#include "OrbbecBlobTracker.generated.h"

class UArrayVisualizer;
class UBlobArrayVisualizer;

struct FOrbbecFrame;
class UOrbbecCameraController;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBlobActorSpawned, AActor*, Actor);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBlobActorDestroyed,AActor*, Actor);

UCLASS(ClassGroup = (FlowerBeds))
class AOrbbecBlobTracker : public AActor
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	FName BlobTrackerName = NAME_None;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UArrayVisualizer> DepthFeedVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UArrayVisualizer> BlobBgVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UArrayVisualizer> BlobFgVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UBlobArrayVisualizer> BlobVisualizer = nullptr;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	TSubclassOf<AActor> BlobActorClass;
	
	UPROPERTY(BlueprintAssignable) 
	FBlobActorSpawned OnBlobActorSpawned;
	
	UPROPERTY(BlueprintAssignable) 
	FBlobActorDestroyed OnBlobActorDestroyed;
	
	DECLARE_MULTICAST_DELEGATE_TwoParams(
		FOnBlobDetectionResult, 
		const AOrbbecBlobTracker*, 
		const II::Vision::FBlobTracker::FDetectionResult&);
	
	FOnBlobDetectionResult OnBlobDetectionResult;
	
	AOrbbecBlobTracker();
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	II::Vision::FBlobTracker BlobTracker;
	
	UPROPERTY(Transient)
	TObjectPtr<UOrbbecCameraController> CameraController;
	
	FDelegateHandle OnFramesReceivedDelegateHandle;
	
	void OnFramesReceived(const FOrbbecFrame& ColorFrame, const FOrbbecFrame& DepthFrame, const FOrbbecFrame& IRFrame);
	
	UPROPERTY(Transient)
	TArray<TObjectPtr<AActor>> BlobActors;
	
	void UpdateWorldBlobs(const TArray<II::Vision::FBlobTracker::FBlob3D>& Blobs);
	
	void DrawBlobDebug(const FVector& WorldPos, const FVector& WorldHalfExtents) const;
};