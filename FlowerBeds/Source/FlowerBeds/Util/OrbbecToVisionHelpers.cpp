#include "OrbbecToVisionHelpers.h"

#include "OrbbecSensor/Device/OrbbecCameraController.h"
#include "IIVision/FramePacket.h"

namespace II::Util
{
	Vision::FFramePacket OrbbecToVisionFrame(const FOrbbecFrame& Frame)
	{
		Vision::FFramePacket DepthFrame;
		DepthFrame.Width = Frame.Config.Width;
		DepthFrame.Height = Frame.Config.Height;
		DepthFrame.TimestampUs = Frame.TimestampUs;
		DepthFrame.Data = Frame.Data;
		DepthFrame.Intrinsics = { Frame.Config.Fx, Frame.Config.Fy, Frame.Config.Cx, Frame.Config.Cy };
		return DepthFrame;
	}
}
