#include "FlowerBedCoordinator.h"

#include "BlobTrackerSettings.h"
#include "FlowerBeds.h"
#include "FlowerBedSettings.h"
#include "OrbbecBlobTracker.h"
#include "Kismet/GameplayStatics.h"

AFlowerBedCoordinator::AFlowerBedCoordinator()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AFlowerBedCoordinator::BeginPlay()
{
	Super::BeginPlay();
	
	CreateBlobTrackersFromSettings();
	CreateFlowerModulesFromSettings();
	CreateFlowerControllersFromSettings();
}

void AFlowerBedCoordinator::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
}

void AFlowerBedCoordinator::CreateBlobTrackersFromSettings()
{
	const UBlobTrackerSettings* BlobTrackerSettings = GetDefault<UBlobTrackerSettings>();
	
	if (!BlobTrackerSettings)
	{
		UE_LOG(LogFlowerBeds, Error, TEXT("AFlowerBedCoordinator: Failed to retrieve blob tracker settings."));
		return;
	}
	
	for (const FBlobTrackerConfig& BlobTrackerConfig : BlobTrackerSettings->BlobTrackers)
	{
		FActorSpawnParameters SpawnParams;
		SpawnParams.Owner = this;
		
		FTransform SpawnTransform{ BlobTrackerConfig.Rotation, BlobTrackerConfig.PosCm };
		AOrbbecBlobTracker* SpawnedActor = GetWorld()->SpawnActorDeferred<AOrbbecBlobTracker>(
			BlobTrackerClass, 
			SpawnTransform, 
			this);
		SpawnedActor->BlobTrackerName = BlobTrackerConfig.Name;
		UGameplayStatics::FinishSpawningActor(SpawnedActor, SpawnTransform);
		
		SpawnedActor->OnBlobDetectionResult.AddUObject(this, &AFlowerBedCoordinator::OnBlobDetectionResult);
		
		BlobTrackers.Add(SpawnedActor);
	}
}

void AFlowerBedCoordinator::OnBlobDetectionResult(
	const AOrbbecBlobTracker* BlobTracker,
	const II::Vision::FBlobTracker::FDetectionResult& DetectionResult)
{
	TArray<FVector> BlobTargets;
	
	for (const auto& Blob : DetectionResult.WorldSpaceBlobs)
	{
		const FVector WorldPos = BlobTracker->GetActorTransform().TransformPosition(Blob.GetWorldPosCm());
		BlobTargets.Emplace(WorldPos);
	}
	
	TArray<AFlowerCluster::FUpdateTargetResult> UpdateResults;
	
	for (const AFlowerModule* FlowerModule : FlowerModules)
	{
		FlowerModule->UpdateClusterTargets(BlobTargets, UpdateResults);
	}
	
	for (const AFlowerCluster::FUpdateTargetResult& UpdateResult : UpdateResults)
	{
		for (UFlowerController* FlowerController : FlowerControllers)
		{
			FlowerController->SendFlowerRotation(UpdateResult.OscAddress, UpdateResult.Rotation);
		}
	}
}

void AFlowerBedCoordinator::CreateFlowerModulesFromSettings()
{
	const UFlowerBedSettings* FlowerBedSettings = GetDefault<UFlowerBedSettings>();
	
	if (!FlowerBedSettings)
	{
		UE_LOG(LogFlowerBeds, Error, TEXT("AFlowerBedCoordinator: Failed to retrieve flower bed settings."));
		return;
	}
	
	for (const FFlowerModuleConfig& FlowerModuleConfig : FlowerBedSettings->FlowerModules)
	{
		FActorSpawnParameters SpawnParams;
		SpawnParams.Owner = this;
		AFlowerModule* SpawnedActor = GetWorld()->SpawnActor<AFlowerModule>(
			FlowerModuleClass,
			FVector::ZeroVector,
			FRotator::ZeroRotator,
			SpawnParams);
		SpawnedActor->Init(FlowerModuleConfig);
		FlowerModules.Add(SpawnedActor);
	}
}

void AFlowerBedCoordinator::CreateFlowerControllersFromSettings()
{
	const UFlowerBedSettings* FlowerBedSettings = GetDefault<UFlowerBedSettings>();
	
	if (!FlowerBedSettings)
	{
		UE_LOG(LogFlowerBeds, Error, TEXT("AFlowerBedCoordinator: Failed to retrieve flower bed settings."));
		return;
	}
	
	for (const FFlowerControllerConfig& FlowerControllerConfig : FlowerBedSettings->FlowerControllers)
	{
		UFlowerController* FlowerController = NewObject<UFlowerController>(this);
		FlowerController->Init(FlowerControllerConfig);
		FlowerControllers.Add(FlowerController);
	}
}
