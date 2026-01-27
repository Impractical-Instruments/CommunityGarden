#pragma once

#include "DepthFrame.h"

namespace II::Vision
{
	class FBlobTracker
	{
	public:
		void BeginCalibration();
		void PushCalibrationFrame(const FDepthFrame& Frame);
		void EndCalibration();
		
	private:
		uint32 Width = 0;
		uint32 Height = 0;
		TArray<uint16> BackgroundDepthMm{};
		TArray<bool> ValidMask{};
	};
}