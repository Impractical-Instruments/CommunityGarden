#pragma once

#include "FramePacket.h"

namespace II::Vision
{
	class IIVISION_API FBlobTracker
	{
	public:
		void BeginCalibration(int32 NumCalibrationFrames, int32 InWidth, int32 InHeight);
		void PushCalibrationFrame(const FFramePacket& Frame);
		
		enum class ECalibrationState : uint8
		{
			NotCalibrated,
			CalibrationInProgress,
			Calibrated
		};
		
		ECalibrationState GetCalibrationState() const;
		
		int32 GetWidth() const;
		int32 GetHeight() const;
		const TArray<uint16>& GetBackgroundDepthMm() const;
		const TArray<bool>& GetValidMask() const;
		
	private:
		constexpr static int32 MaxCalibrationFrames = 128;
		constexpr static int32 MinFramesValid = 10;
		
		// NB: CalibrationFrames is stored in contiguous memory for speed
		TArray<uint16> CalibrationFrames{};
		int32 Width = 0;
		int32 Height = 0;
		int32 NumCalibrationFramesRemaining = 0;
		
		TArray<uint16> BackgroundDepthMm{};
		TArray<bool> ValidMask{};
		
		ECalibrationState CalibrationState = ECalibrationState::NotCalibrated;
		
		void EndCalibration();
		void ComputeBackground();
	};
}