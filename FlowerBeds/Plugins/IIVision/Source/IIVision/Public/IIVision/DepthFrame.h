#pragma once

namespace II::Vision
{
	struct FDepthFrame
	{
		int32 Width = 0;
		int32 Height = 0;
		TArray<uint16> DepthMm{};
		uint64 TimestampUs = 0;
	};
}