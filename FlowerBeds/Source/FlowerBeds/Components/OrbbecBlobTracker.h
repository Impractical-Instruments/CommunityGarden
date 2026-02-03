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

UCLASS(ClassGroup = (FlowerBeds), meta = (BlueprintSpawnableComponent))
class UOrbbecBlobTracker : public UActorComponent
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UArrayVisualizer> DepthFeedVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UArrayVisualizer> BlobBgVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UArrayVisualizer> BlobFgVisualizer = nullptr;
	
	UPROPERTY(BlueprintReadWrite, Category = "Flower Beds")
	TObjectPtr<UBlobArrayVisualizer> BlobVisualizer = nullptr;
	
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Flower Beds")
	TSubclassOf<AActor> BlobActorClass;
	
	UPROPERTY(BlueprintAssignable) 
	FBlobActorSpawned OnBlobActorSpawned;
	
	UPROPERTY(BlueprintAssignable) 
	FBlobActorDestroyed OnBlobActorDestroyed;
	
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