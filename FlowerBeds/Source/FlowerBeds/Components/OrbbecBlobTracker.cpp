#include "OrbbecBlobTracker.h"

#include "ArrayVisualizer.h"
#include "FlowerBeds/BlobTrackerSettings.h"
#include "FlowerBeds/FlowerBeds.h"
#include "FlowerBeds/Util/OrbbecToVisionHelpers.h"
#include "IIVision/BlobArrayVisualizer.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"

AOrbbecBlobTracker::AOrbbecBlobTracker()
{
	CameraController = CreateDefaultSubobject<UOrbbecCameraController>("CameraController");
}

void AOrbbecBlobTracker::BeginPlay()
{
	Super::BeginPlay();
	
	// Find the config for this blob tracker and apply it
	const UBlobTrackerSettings* BlobTrackerSettings = GetDefault<UBlobTrackerSettings>();
	
	if (!BlobTrackerSettings)
	{
		UE_LOG(LogFlowerBeds, Error, TEXT("UOrbbecBlobTracker: Failed to retrieve blob tracker settings."));
		return;
	}
	
	if (const FBlobTrackerConfig* FoundConfig = BlobTrackerSettings->BlobTrackers.FindByPredicate(
		[Name = BlobTrackerName](const FBlobTrackerConfig& Config)
		{
			return Config.Name == Name;
		}))
	{
		// Set position
		SetActorLocation(FoundConfig->PosCm);
		SetActorRotation(FoundConfig->Rotation);
		
		// Set the camera config
		CameraController->CameraConfig = FoundConfig->CameraConfig;
	}
	
	check(CameraController);
	OnFramesReceivedDelegateHandle = 
		CameraController->OnFramesReceivedNative.AddUObject(this, &AOrbbecBlobTracker::OnFramesReceived);
	CameraController->StartCamera();
}

void AOrbbecBlobTracker::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (CameraController)
	{
		CameraController->OnFramesReceivedNative.Remove(OnFramesReceivedDelegateHandle);
	}
	
	Super::EndPlay(EndPlayReason);
}

void AOrbbecBlobTracker::OnFramesReceived(
	const FOrbbecFrame& /* ColorFrame */, 
	const FOrbbecFrame& DepthFrame, 
	const FOrbbecFrame& /* IRFrame */)
{
	if (DepthFeedVisualizer)
	{
		DepthFeedVisualizer->InitTexture(DepthFrame.Config.Width, DepthFrame.Config.Height, PF_G16, false);
		DepthFeedVisualizer->UpdateTexture(DepthFrame.Data->GetData(), DepthFrame.Config.Width, DepthFrame.Config.Height, PF_G16);
	}
	
	switch (BlobTracker.GetCalibrationState())
	{
	case II::Vision::FBlobTracker::ECalibrationState::NotCalibrated:
		BlobTracker.BeginCalibration(60, DepthFrame.Config.Width, DepthFrame.Config.Height);
		BlobTracker.PushCalibrationFrame(II::Util::OrbbecToVisionFrame(DepthFrame));
		break;
	case II::Vision::FBlobTracker::ECalibrationState::CalibrationInProgress:
		BlobTracker.PushCalibrationFrame(II::Util::OrbbecToVisionFrame(DepthFrame));
		
		// If we just completed calibration, update the background depth map
		if (BlobTracker.GetCalibrationState() == II::Vision::FBlobTracker::ECalibrationState::Calibrated)
		{
			if (BlobBgVisualizer)
			{
				BlobBgVisualizer->InitTexture(BlobTracker.GetWidth(), BlobTracker.GetHeight(), PF_G16, false);
				BlobBgVisualizer->UpdateTexture(
					reinterpret_cast<const uint8*>(BlobTracker.GetBackgroundDepthMm().GetData()), 
					BlobTracker.GetWidth(), 
					BlobTracker.GetHeight(), 
					PF_G16);
			}
		}
		break;
	case II::Vision::FBlobTracker::ECalibrationState::Calibrated:
		II::Vision::FBlobTracker::FDetectionResult DetectionResult;
		BlobTracker.Detect(II::Util::OrbbecToVisionFrame(DepthFrame), DetectionResult);
		
		if (BlobFgVisualizer)
		{
			BlobFgVisualizer->InitTexture(BlobTracker.GetWidth(), BlobTracker.GetHeight(), PF_G8, false);
			BlobFgVisualizer->UpdateTexture(DetectionResult.Foreground.GetData(), BlobTracker.GetWidth(), BlobTracker.GetHeight(), PF_G8);
		}
		
		if (BlobVisualizer)
		{
			BlobVisualizer->InitTexture(BlobTracker.GetWidth(), BlobTracker.GetHeight());
			BlobVisualizer->UpdateTexture(DetectionResult.ScreenSpaceBlobs);
		}
		
		UpdateWorldBlobs(DetectionResult.WorldSpaceBlobs);
		
		break;
	}
}

void AOrbbecBlobTracker::UpdateWorldBlobs(const TArray<II::Vision::FBlobTracker::FBlob3D>& Blobs)
{
	int32 BlobIdx = 0;
	
	for (const auto& Blob : Blobs)
	{
		// Transform to world space
		const FTransform WorldTransform = GetActorTransform();
		const FVector WorldPos = WorldTransform.TransformPosition(Blob.GetWorldPosCm());
		const FVector WorldHalfExtents = WorldTransform.TransformVector(Blob.GetWorldHalfExtentsCm());
		
		DrawBlobDebug(WorldPos, WorldHalfExtents);
		
		if (BlobIdx < BlobActors.Num())
		{
			BlobActors[BlobIdx]->SetActorHiddenInGame(false);
			BlobActors[BlobIdx]->SetActorLocation(WorldPos);
		}
		else
		{
			FActorSpawnParameters SpawnParams;
			SpawnParams.Owner = this;
			BlobActors.Emplace(
				GetWorld()->SpawnActor<AActor>(BlobActorClass, WorldPos, FRotator::ZeroRotator, SpawnParams));
			
			OnBlobActorSpawned.Broadcast(BlobActors.Last());
		}
		
		++BlobIdx;
	}
	
	// Disable any extras
	for (; BlobIdx < BlobActors.Num(); ++BlobIdx)
	{
		BlobActors[BlobIdx]->SetActorHiddenInGame(true);
	}
}

void AOrbbecBlobTracker::DrawBlobDebug(const FVector& WorldPos, const FVector& WorldHalfExtents) const
{
	const UWorld* World = GetWorld();
	
	if (!World)
	{
		return;
	}
	
	DrawDebugBox(
		World, 
		WorldPos,
		WorldHalfExtents,
		FColor::Cyan,
		false, 
		0.1f,
		0,
		1.5f);
}
