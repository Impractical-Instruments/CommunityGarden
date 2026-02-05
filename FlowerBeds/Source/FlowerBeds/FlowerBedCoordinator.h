#pragma once

#include "CoreMinimal.h"
#include "OrbbecToVisionHelpers.h"
#include "IIVision/BlobTracker.h"

#include "FlowerBedCoordinator.generated.h"

class AFlowerCluster;
class UFlowerController;
class AFlowerModule;
class AOrbbecBlobTracker;

UCLASS(ClassGroup = (FlowerBeds))
class AFlowerBedCoordinator : public AActor
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	TSubclassOf<AOrbbecBlobTracker> BlobTrackerClass;
	
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Flower Beds")
	TSubclassOf<AFlowerModule> FlowerModuleClass;
	
	AFlowerBedCoordinator();
	
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	
private:
	UPROPERTY(Transient)
	TArray<TObjectPtr<AOrbbecBlobTracker>> BlobTrackers;
	
	void CreateBlobTrackersFromSettings();
	void OnBlobDetectionResult(
		const AOrbbecBlobTracker* BlobTracker, 
		const II::Vision::FBlobTracker::FDetectionResult& DetectionResult);
	
	UPROPERTY(Transient)
	TArray<TObjectPtr<AFlowerModule>> FlowerModules;
	
	void CreateFlowerModulesFromSettings();
	
	UPROPERTY(Transient)
	TArray<TObjectPtr<UFlowerController>> FlowerControllers;
	
	void CreateFlowerControllersFromSettings();
};
