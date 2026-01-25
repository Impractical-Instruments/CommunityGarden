#include "OrbbecSensor/Device/OrbbecCameraController.h"
#include "Async/Async.h"

#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
#endif

#include "libobsensor/ObSensor.hpp"

struct UOrbbecCameraController::FOrbbecImplementation
{
	std::shared_ptr<ob::Pipeline> Pipeline;
	std::shared_ptr<ob::Config> Config;

	static OBFormat MapFormat(EOrbbecFrameFormat Format)
	{
		switch (Format)
		{
		case EOrbbecFrameFormat::YUYV: return OB_FORMAT_YUYV;
		case EOrbbecFrameFormat::MJPG: return OB_FORMAT_MJPG;
		case EOrbbecFrameFormat::Y16:  return OB_FORMAT_Y16;
		case EOrbbecFrameFormat::RGB:  return OB_FORMAT_RGB;
		case EOrbbecFrameFormat::BGR:  return OB_FORMAT_BGR;
		case EOrbbecFrameFormat::BGRA: return OB_FORMAT_BGRA;
		case EOrbbecFrameFormat::RGBA: return OB_FORMAT_RGBA;
		default: return OB_FORMAT_UNKNOWN;
		}
	}

	static EOrbbecFrameFormat MapFormatBack(OBFormat Format)
	{
		switch (Format)
		{
		case OB_FORMAT_YUYV: return EOrbbecFrameFormat::YUYV;
		case OB_FORMAT_MJPG: return EOrbbecFrameFormat::MJPG;
		case OB_FORMAT_Y16:  return EOrbbecFrameFormat::Y16;
		case OB_FORMAT_RGB:  return EOrbbecFrameFormat::RGB;
		case OB_FORMAT_BGR:  return EOrbbecFrameFormat::BGR;
		case OB_FORMAT_BGRA: return EOrbbecFrameFormat::BGRA;
		case OB_FORMAT_RGBA: return EOrbbecFrameFormat::RGBA;
		default: return EOrbbecFrameFormat::Unknown;
		}
	}
};

UOrbbecCameraController::UOrbbecCameraController()
	: Implementation(MakeUnique<FOrbbecImplementation>())
{
}

UOrbbecCameraController::~UOrbbecCameraController()
{
	StopCamera();
}

UOrbbecCameraController::UOrbbecCameraController(FVTableHelper& Helper)
	: Super(Helper)
{
}

bool UOrbbecCameraController::StartCamera(const FOrbbecVideoConfig& ColorConfig, const FOrbbecVideoConfig& DepthConfig, const FOrbbecVideoConfig& IRConfig)
{
	if (!Implementation) return false;

	try
	{
		Implementation->Pipeline = std::make_shared<ob::Pipeline>();
		Implementation->Config = std::make_shared<ob::Config>();

		auto SetupStream = [this](const FOrbbecVideoConfig& Config, OBStreamType StreamType) {
			if (Config.Width > 0 || Config.Height > 0 || Config.FPS > 0 || Config.Format != EOrbbecFrameFormat::Unknown)
			{
				Implementation->Config->enableVideoStream(StreamType, 
					Config.Width > 0 ? Config.Width : OB_WIDTH_ANY, 
					Config.Height > 0 ? Config.Height : OB_HEIGHT_ANY, 
					Config.FPS > 0 ? Config.FPS : OB_FPS_ANY, 
					FOrbbecImplementation::MapFormat(Config.Format));
			}
		};

		SetupStream(ColorConfig, OB_STREAM_COLOR);
		SetupStream(DepthConfig, OB_STREAM_DEPTH);
		SetupStream(IRConfig, OB_STREAM_IR);

		Implementation->Pipeline->start(Implementation->Config, [this](std::shared_ptr<ob::FrameSet> FrameSet) {
			if (!FrameSet) return;

			auto ProcessFrame = [this](std::shared_ptr<ob::Frame> Frame, OBFrameType FrameType) {
				if (Frame && Frame->dataSize() > 0)
				{
					auto VideoFrame = Frame->as<ob::VideoFrame>();
					if (VideoFrame)
					{
						int32 Width = VideoFrame->width();
						int32 Height = VideoFrame->height();
						EOrbbecFrameFormat Format = FOrbbecImplementation::MapFormatBack(VideoFrame->getFormat());

						TArray<uint8> Data;
						Data.SetNumUninitialized(Frame->dataSize());
						FMemory::Memcpy(Data.GetData(), Frame->data(), Frame->dataSize());

						AsyncTask(ENamedThreads::GameThread, [this, Data = MoveTemp(Data), Width, Height, Format, FrameType]() {
							// Check if the object is still valid before broadcasting
							if (IsValid(this))
							{
								if (FrameType == OB_FRAME_COLOR) OnColorFrameReceived.Broadcast(Data, Width, Height, Format);
								else if (FrameType == OB_FRAME_DEPTH) OnDepthFrameReceived.Broadcast(Data, Width, Height, Format);
								else if (FrameType == OB_FRAME_IR) OnIRFrameReceived.Broadcast(Data, Width, Height, Format);
							}
						});
					}
				}
			};

			ProcessFrame(FrameSet->colorFrame(), OB_FRAME_COLOR);
			ProcessFrame(FrameSet->depthFrame(), OB_FRAME_DEPTH);
			ProcessFrame(FrameSet->irFrame(), OB_FRAME_IR);
		});

		return true;
	}
	catch (ob::Error& e)
	{
		UE_LOG(LogTemp, Error, TEXT("OrbbecSDK Error: %s"), *FString(e.getMessage()));
		return false;
	}
}

void UOrbbecCameraController::StopCamera()
{
	if (Implementation && Implementation->Pipeline)
	{
		try
		{
			Implementation->Pipeline->stop();
		}
		catch (ob::Error& e)
		{
			UE_LOG(LogTemp, Warning, TEXT("OrbbecSDK Error during stop: %s"), *FString(e.getMessage()));
		}
		Implementation->Pipeline.reset();
		Implementation->Config.reset();
	}
}
