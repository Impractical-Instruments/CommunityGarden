#include "OrbbecBlobTracker.h"

#include "FlowerBeds/FlowerBeds.h"
#include "FlowerBeds/Util/OrbbecToVisionHelpers.h"
#include "IIVision/BlobTrackerVisualizer.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"

void UOrbbecBlobTracker::BeginPlay()
{
	Super::BeginPlay();
	
	UOrbbecCameraController* CameraController = GetCameraController();
	
	if (!CameraController)
	{
		UE_LOG(LogFlowerBeds, Error, TEXT("UOrbbecBlobTracker: A camera controller (UOrbbecCameraController) is required."));
		return;
	}
	
	OnFramesReceivedDelegateHandle = 
		CameraController->OnFramesReceivedNative.AddUObject(this, &UOrbbecBlobTracker::OnFramesReceived);
	CameraController->StartCamera();
	
	BlobTrackerVisualizer = NewObject<UBlobTrackerVisualizer>(this);
}

void UOrbbecBlobTracker::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UOrbbecCameraController* CameraController = GetCameraController())
	{
		CameraController->OnFramesReceivedNative.Remove(OnFramesReceivedDelegateHandle);
	}
	
	Super::EndPlay(EndPlayReason);
}

void UOrbbecBlobTracker::OnFramesReceived(
	const FOrbbecFrame& /* ColorFrame */, 
	const FOrbbecFrame& DepthFrame, 
	const FOrbbecFrame& /* IRFrame */)
{
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
			BlobTrackerVisualizer->SetBackgroundDepthMap(
				BlobTracker.GetBackgroundDepthMm(),
				BlobTracker.GetWidth(),
				BlobTracker.GetHeight());
		}
		break;
	case II::Vision::FBlobTracker::ECalibrationState::Calibrated:
		// TODO: actually do blob tracking
		break;
	}
}

UOrbbecCameraController* UOrbbecBlobTracker::GetCameraController() const
{
	return GetOwner()->FindComponentByClass<UOrbbecCameraController>();
}
