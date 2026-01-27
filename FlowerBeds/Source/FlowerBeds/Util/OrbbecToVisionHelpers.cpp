#include "OrbbecToVisionHelpers.h"

#include "FlowerBeds/FlowerBeds.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"
#include "IIVision/DepthFrame.h"

namespace II::Util
{
	Vision::FDepthFrame OrbbecToVisionDepthFrame(const FOrbbecFrame& Frame)
	{
		Vision::FDepthFrame DepthFrame;
		DepthFrame.Width = Frame.Config.Width;
		DepthFrame.Height = Frame.Config.Height;
		DepthFrame.TimestampUs = Frame.TimestampUs;
		
		// Convert to uint16 depth in mm if it's not already in that format
		// NB: for now, we only support Y16 anyway
		const auto NumPixels = DepthFrame.Width * DepthFrame.Height;
		DepthFrame.DepthMm.SetNumUninitialized(NumPixels);
		
		switch (Frame.Config.Format)
		{
		case EOrbbecFrameFormat::Y16:
			if (!ensure(Frame.Data.Num() == NumPixels * 2))
			{
				UE_LOG(
					LogFlowerBeds,
					Warning,
					TEXT("Orbbec frame data size mismatch: expected %d and got %d"),
					NumPixels * 2,
					Frame.Data.Num());
				return {};
			}
			FMemory::Memcpy(DepthFrame.DepthMm.GetData(), Frame.Data.GetData(), NumPixels * sizeof(uint16));
			break;
		default:
			UE_LOG(LogFlowerBeds, Warning, TEXT("Unsupported Orbbec frame format: %d"), static_cast<int32>(Frame.Config.Format));
			return {};
		}
		
		return DepthFrame;
	}
}
