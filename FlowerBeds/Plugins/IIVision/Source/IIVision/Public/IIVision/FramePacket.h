#pragma once

namespace II::Vision
{
	struct IIVISION_API FCameraIntrinsics
	{
		float Fx = 0;
		float Fy = 0;
		float Cx = 0;
		float Cy = 0;
	};
	
	struct IIVISION_API FFramePacket
	{
		int32 Width = 0;
		int32 Height = 0;
		uint64 TimestampUs = 0;
		TSharedPtr<TArray<uint8>> Data{};
		FCameraIntrinsics Intrinsics{};
	};
}