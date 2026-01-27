#pragma once

struct FOrbbecFrame;

namespace II::Vision
{
	struct FFramePacket;
}

namespace II::Util
{
	Vision::FFramePacket OrbbecToVisionFrame(const FOrbbecFrame& Frame);
}
