#include "IIVision/BlobTracker.h"

#include "IIVision/IIVisionModule.h"

namespace II::Vision
{
	void FBlobTracker::BeginCalibration(int32 NumCalibrationFrames, int32 InWidth, int32 InHeight)
	{
		// Invalidate state
		BackgroundDepthMm.Reset();
		ValidMask.Reset();
		
		// Reserve calibration frame space
		NumCalibrationFramesRemaining = FMath::Clamp(1, NumCalibrationFrames, MaxCalibrationFrames);
		this->Width = FMath::Max(1, InWidth);
		this->Height = FMath::Max(1, InHeight);
		CalibrationFrames.Reset(NumCalibrationFrames * InWidth * InHeight);
		
		CalibrationState = ECalibrationState::CalibrationInProgress;
	}

	void FBlobTracker::PushCalibrationFrame(const FFramePacket& Frame)
	{
		if (CalibrationState != ECalibrationState::CalibrationInProgress)
		{
			UE_LOG(LogIIVision, Warning, TEXT("Calibration frame received in invalid state (%d)"), (int32)CalibrationState);
			return;
		}
		
		if (NumCalibrationFramesRemaining <= 0)
		{
			UE_LOG(LogIIVision, Warning, TEXT("Calibration frame received after end of calibration"));
			return;
		}
		
		if (Frame.Width != Width || Frame.Height != Height)
		{
			UE_LOG(LogIIVision, Warning, TEXT("Calibration frame size mismatch. Expected (%d, %d), got (%d, %d)"), Width, Height, Frame.Width, Frame.Height);
			return;
		}
		
		// Copy the frame data into the calibration buffer
		CalibrationFrames.Append(*Frame.Data);
		
		if (--NumCalibrationFramesRemaining <= 0)
		{
			EndCalibration();
		}
	}

	FBlobTracker::ECalibrationState FBlobTracker::GetCalibrationState() const
	{
		return CalibrationState;
	}

	TArray<uint16> FBlobTracker::GetBackgroundDepthMm() const
	{
		if (CalibrationState != ECalibrationState::Calibrated)
		{
			return {};
		}
		
		return BackgroundDepthMm;
	}
	
	TArray<bool> FBlobTracker::GetValidMask() const
	{
		if (CalibrationState != ECalibrationState::Calibrated)
		{
			return {};
		}
		
		return ValidMask;
	}
	
	void FBlobTracker::EndCalibration()
	{
		ComputeBackground();
		CalibrationFrames.Empty();
	}

	void FBlobTracker::ComputeBackground()
	{
		const int32 NumPixels = Width * Height;
		const int32 NumCalibrationFrames = CalibrationFrames.Num() / NumPixels;
		
		uint16 Samples[MaxCalibrationFrames];
		
		BackgroundDepthMm.SetNumUninitialized(NumPixels);
		ValidMask.SetNumUninitialized(NumPixels);
		
		for (int32 PixelIdx = 0; PixelIdx < NumPixels; ++PixelIdx)
		{
			int32 NumValidSamples = 0;
			
			for (int32 FrameIdx = 0; FrameIdx < NumCalibrationFrames; ++FrameIdx)
			{
				const int32 SampleIdx = PixelIdx + FrameIdx * NumPixels;
				const uint16 DepthMm = CalibrationFrames[SampleIdx];
				if (DepthMm > 0)
				{
					Samples[NumValidSamples++] = CalibrationFrames[SampleIdx];
				}
			}
			
			if (NumValidSamples >= MinFramesValid)
			{
				// Find the median of the valid samples
				std::nth_element(Samples, Samples + NumValidSamples / 2, Samples + NumValidSamples);
				BackgroundDepthMm[PixelIdx] = Samples[NumValidSamples / 2];
				ValidMask[PixelIdx] = true;
			}
			else
			{
				BackgroundDepthMm[PixelIdx] = 0;
				ValidMask[PixelIdx] = false;
			}
		}
		
		CalibrationState = ECalibrationState::Calibrated;
	}
}
