#pragma once

struct FOrbbecFrame;

namespace II::Vision
{
	struct FDepthFrame;
}

namespace II::Util
{
	Vision::FDepthFrame OrbbecToVisionDepthFrame(const FOrbbecFrame& Frame);
}
