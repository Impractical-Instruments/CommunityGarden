#include "OrbbecBlobTracker.h"

#include "FlowerBeds/FlowerBeds.h"
#include "FlowerBeds/Util/OrbbecToVisionHelpers.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"

void UOrbbecBlobTracker::BeginPlay()
{
	Super::BeginPlay();
	
	if (!CameraController)
	{
		UE_LOG(LogFlowerBeds, Error, TEXT("UOrbbecBlobTracker: Camera controller not set."));
		return;
	}
	
	OnFramesReceivedDelegateHandle = 
		CameraController->OnFramesReceivedNative.AddUObject(this, &UOrbbecBlobTracker::OnFramesReceived);
	CameraController->StartCamera();
}

void UOrbbecBlobTracker::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (CameraController)
	{
		CameraController->OnFramesReceivedNative.Remove(OnFramesReceivedDelegateHandle);
	}
	
	Super::EndPlay(EndPlayReason);
}

void UOrbbecBlobTracker::OnFramesReceived(
	const FOrbbecFrame& ColorFrame, 
	const FOrbbecFrame& DepthFrame, 
	const FOrbbecFrame& IRFrame)
{
	switch (BlobTracker.GetCalibrationState())
	{
	case II::Vision::FBlobTracker::ECalibrationState::NotCalibrated:
		BlobTracker.BeginCalibration(60, DepthFrame.Config.Width, DepthFrame.Config.Height);
		BlobTracker.PushCalibrationFrame(II::Util::OrbbecToVisionFrame(DepthFrame));
		break;
	case II::Vision::FBlobTracker::ECalibrationState::CalibrationInProgress:
		BlobTracker.PushCalibrationFrame(II::Util::OrbbecToVisionFrame(DepthFrame));
		break;
	case II::Vision::FBlobTracker::ECalibrationState::Calibrated:
		// TODO: actually do blob tracking
		break;
	}
}
