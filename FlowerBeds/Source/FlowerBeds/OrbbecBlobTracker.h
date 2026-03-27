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
	// Represents a blob that has been matched across at least one frame and has a stable identity.
	struct FActiveBlob
	{
		uint32 StableId;
		// Camera-relative world position (from FBlob3D::GetWorldPosCm()) at last detection.
		FVector LastPosCm;
		int32 MissedFrames = 0;
	};


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

	// --- Stable ID tracking ---
	// Maximum distance (cm) a blob may move between frames and still match the same identity.
	static constexpr float MaxMatchDistanceCm = 80.f;
	// Number of consecutive missed frames before an active blob's identity is retired.
	static constexpr int32 MaxMissedFrames = 15;

	TArray<FActiveBlob> ActiveBlobs;
	uint32 NextStableId = 0;

	// Matches new detection results against ActiveBlobs and fills FBlob3D::StableId on each valid blob.
	void AssignStableIds(II::Vision::FBlobTracker::FDetectionResult& Result);

	// --- Blob actors ---
	UPROPERTY(Transient)
	TMap<uint32, TObjectPtr<AActor>> BlobActorMap;

	void UpdateWorldBlobs(const TArray<II::Vision::FBlobTracker::FBlob3D>& Blobs);

	void DrawBlobDebug(const FVector& WorldPos, const FVector& WorldHalfExtents) const;
};