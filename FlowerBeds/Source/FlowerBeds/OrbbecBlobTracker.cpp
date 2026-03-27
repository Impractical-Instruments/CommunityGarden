#include "OrbbecBlobTracker.h"

#include "ArrayVisualizer.h"
#include "FlowerBeds/BlobTrackerSettings.h"
#include "FlowerBeds/FlowerBeds.h"
#include "FlowerBeds/OrbbecToVisionHelpers.h"
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
		UE_LOG(LogFlowerBeds, Error, TEXT("Failed to retrieve blob tracker settings."));
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
		AssignStableIds(DetectionResult);

		OnBlobDetectionResult.Broadcast(this, DetectionResult);
		
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

void AOrbbecBlobTracker::AssignStableIds(II::Vision::FBlobTracker::FDetectionResult& Result)
{
	using FBlob3D = II::Vision::FBlobTracker::FBlob3D;

	// Track which ActiveBlobs were matched this frame so we can age out the rest.
	TBitArray<> Matched(false, ActiveBlobs.Num());

	for (FBlob3D& NewBlob : Result.WorldSpaceBlobs)
	{
		if (!NewBlob.bValid)
		{
			continue;
		}

		const FVector NewPos = NewBlob.GetWorldPosCm();
		float BestDist = MaxMatchDistanceCm;
		int32 BestIdx = INDEX_NONE;

		for (int32 i = 0; i < ActiveBlobs.Num(); ++i)
		{
			if (Matched[i])
			{
				continue;
			}

			const float Dist = FVector::Dist(NewPos, ActiveBlobs[i].LastPosCm);
			if (Dist < BestDist)
			{
				BestDist = Dist;
				BestIdx = i;
			}
		}

		if (BestIdx != INDEX_NONE)
		{
			// Re-use the existing stable identity.
			NewBlob.StableId = ActiveBlobs[BestIdx].StableId;
			ActiveBlobs[BestIdx].LastPosCm = NewPos;
			ActiveBlobs[BestIdx].MissedFrames = 0;
			Matched[BestIdx] = true;
		}
		else
		{
			// New blob — assign a fresh identity and start tracking it.
			NewBlob.StableId = NextStableId++;
			ActiveBlobs.Add({ NewBlob.StableId, NewPos, 0 });
			Matched.Add(true);
		}
	}

	// Age out active blobs that weren't matched this frame; retire after MaxMissedFrames.
	for (int32 i = ActiveBlobs.Num() - 1; i >= 0; --i)
	{
		if (!Matched[i])
		{
			if (++ActiveBlobs[i].MissedFrames > MaxMissedFrames)
			{
				ActiveBlobs.RemoveAtSwap(i);
				// RemoveAtSwap invalidates indices above i, but we're iterating downward so it's safe.
			}
		}
	}
}

void AOrbbecBlobTracker::UpdateWorldBlobs(const TArray<II::Vision::FBlobTracker::FBlob3D>& Blobs)
{
	const FTransform WorldTransform = GetActorTransform();
	TSet<uint32> SeenIds;

	for (const auto& Blob : Blobs)
	{
		if (!Blob.bValid)
		{
			continue;
		}

		const FVector WorldPos = WorldTransform.TransformPosition(Blob.GetWorldPosCm());
		const FVector WorldHalfExtents = WorldTransform.TransformVector(Blob.GetWorldHalfExtentsCm());

		DrawBlobDebug(WorldPos, WorldHalfExtents);

		if (!BlobActorClass)
		{
			continue;
		}

		SeenIds.Add(Blob.StableId);

		if (TObjectPtr<AActor>* Existing = BlobActorMap.Find(Blob.StableId))
		{
			(*Existing)->SetActorHiddenInGame(false);
			(*Existing)->SetActorLocation(WorldPos);
		}
		else
		{
			FActorSpawnParameters SpawnParams;
			SpawnParams.Owner = this;
			AActor* NewActor = GetWorld()->SpawnActor<AActor>(BlobActorClass, WorldPos, FRotator::ZeroRotator, SpawnParams);
			BlobActorMap.Add(Blob.StableId, NewActor);
			OnBlobActorSpawned.Broadcast(NewActor);
		}
	}

	// Hide actors for blobs that weren't detected this frame.
	for (auto& [Id, Actor] : BlobActorMap)
	{
		if (!SeenIds.Contains(Id))
		{
			Actor->SetActorHiddenInGame(true);
		}
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
