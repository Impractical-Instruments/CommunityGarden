#pragma once

#include "FramePacket.h"

namespace II::Vision
{
	class IIVISION_API FBlobTracker
	{
	public:
		struct FCalibrationConfig
		{
			uint16 MinDepthMM = 50;
			uint16 MaxDepthMM = 6000;
		};
		
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
		
		struct FDetectionConfig
		{
			uint16 MinDepthMM = 50;
			uint16 MaxDepthMM = 6000;
			int32 DepthDeltaMM = 80;
			int32 MinBlobPixels = 500;
		};
		
		void ConfigureDetection(FDetectionConfig Config);
		
		struct FDetectionResult
		{
			TArray<uint8> Foreground;
		};
		
		void Detect(const FFramePacket& Frame, FDetectionResult& OutResult);
		
	private:
		constexpr static int32 MaxCalibrationFrames = 128;
		constexpr static int32 MinFramesValid = 10;
		
		// NB: CalibrationFrames is stored in contiguous memory for speed
		FCalibrationConfig CalibrationConfig{};
		TArray<uint16> CalibrationFrames{};
		int32 Width = 0;
		int32 Height = 0;
		int32 NumCalibrationFramesRemaining = 0;
		
		TArray<uint16> BackgroundDepthMm{};
		TArray<bool> ValidMask{};
		
		ECalibrationState CalibrationState = ECalibrationState::NotCalibrated;
		
		FDetectionConfig DetectionConfig{};
		
		void EndCalibration();
		void ComputeBackground();
	};
}
