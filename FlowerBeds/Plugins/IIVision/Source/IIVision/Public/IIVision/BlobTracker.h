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
			uint16 MinDepthMM = 500;
			uint16 MaxDepthMM = 6000;
			int32 DepthDeltaMM = 80;
			int32 MinBlobPixels = 500;
			int32 StridePixels = 3;
			int32 MinSamples = 40;
			int32 ZWindowMm = 150;
		};
		
		void ConfigureDetection(FDetectionConfig Config);
		
		struct FBlob2D
		{
			int32 Id = -1;
			int32 PixelCount = 0;
			int32 MinX = TNumericLimits<int32>::Max();
			int32 MaxX = 0;
			int32 MinY = TNumericLimits<int32>::Max();
			int32 MaxY = 0;
			int64 SumX = 0;
			int64 SumY = 0;
			
			void AddPixel(int32 X, int32 Y);
			
			FVector2f GetCentroid() const;
		};
		
		struct IIVISION_API FBlob3D
		{
			bool bValid = false;
			int32 Id = -1;
			
			// In camera coordinate space
			FVector CamPosMeters = FVector::ZeroVector;
			FVector CamHalfExtentsMeters = FVector::ZeroVector;
			float MedianZMeters = 0.0f;
			int32 SampleCount = 0;
			
			// In UE coordinate space
			FVector GetWorldPosCm() const;
		};
		
		struct FDetectionResult
		{
			TArray<uint8> Foreground;
			TArray<FBlob2D> ScreenSpaceBlobs;
			TArray<FBlob3D> WorldSpaceBlobs;
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
		
		void EndCalibration();
		void ComputeBackground();
		
		TArray<uint16> BackgroundDepthMm{};
		TArray<bool> ValidMask{};
		
		ECalibrationState CalibrationState = ECalibrationState::NotCalibrated;
		
		FDetectionConfig DetectionConfig{};
		TArray<uint8> ForegroundScratchBuffer{};
		
		void SubtractBackground(const FFramePacket& Frame, FDetectionResult& OutResult) const;
		void MajorityFilter(const TArray<uint8>& Src, TArray<uint8>& Dst) const;
		void ExtractBlobs(const TArray<uint8>& Foreground, TArray<FBlob2D>& OutBlobs) const;
		void Compute3DBlobs(
			const TArray<FBlob2D>& ScreenSpaceBlobs, 
			TArray<FBlob3D>& OutBlobs, 
			const FCameraIntrinsics& CameraIntrinsics) const;
	};
}
