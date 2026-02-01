#include "IIVision/BlobTracker.h"

#include "IIVision/IIVisionModule.h"

namespace II::Vision
{
	void FBlobTracker::BeginCalibration(int32 NumCalibrationFrames, int32 InWidth, int32 InHeight)
	{
		// Invalidate state
		BackgroundDepthMm.Reset();
		ValidMask.Reset();
		
		// Reserve calibration frame space
		NumCalibrationFramesRemaining = FMath::Max(1, NumCalibrationFrames);
		this->Width = FMath::Max(1, InWidth);
		this->Height = FMath::Max(1, InHeight);
		CalibrationFrames.Reset(NumCalibrationFrames * InWidth * InHeight);
		
		CalibrationState = ECalibrationState::CalibrationInProgress;
	}

	void FBlobTracker::PushCalibrationFrame(const FFramePacket& Frame)
	{
		if (CalibrationState != ECalibrationState::CalibrationInProgress)
		{
			UE_LOG(LogIIVision, Warning, TEXT("Calibration frame received in invalid state (%d)"), (int32)CalibrationState);
			return;
		}
		
		if (NumCalibrationFramesRemaining <= 0)
		{
			UE_LOG(LogIIVision, Warning, TEXT("Calibration frame received after end of calibration"));
			return;
		}
		
		if (Frame.Width != Width || Frame.Height != Height)
		{
			UE_LOG(LogIIVision, Warning, TEXT("Calibration frame size mismatch. Expected (%d, %d), got (%d, %d)"), Width, Height, Frame.Width, Frame.Height);
			return;
		}
		
		// Copy the frame data into the calibration buffer
		check(Frame.Data->Num() == Width * Height * sizeof(uint16));
		const auto SrcPtr = Frame.Data->GetData();
		const auto DstPtr = CalibrationFrames.GetData() + CalibrationFrames.Num();
		CalibrationFrames.AddUninitialized(Width * Height);
		FMemory::Memcpy(DstPtr, SrcPtr, Width * Height * sizeof(uint16));
		
		if (--NumCalibrationFramesRemaining <= 0)
		{
			EndCalibration();
		}
	}

	FBlobTracker::ECalibrationState FBlobTracker::GetCalibrationState() const
	{
		return CalibrationState;
	}

	int32 FBlobTracker::GetWidth() const
	{
		return Width;
	}

	int32 FBlobTracker::GetHeight() const
	{
		return Height;
	}

	const TArray<uint16>& FBlobTracker::GetBackgroundDepthMm() const
	{
		return BackgroundDepthMm;
	}
	
	const TArray<bool>& FBlobTracker::GetValidMask() const
	{
		return ValidMask;
	}

	void FBlobTracker::ConfigureDetection(FDetectionConfig Config)
	{
		DetectionConfig = MoveTemp(Config);
	}

	void FBlobTracker::Detect(const FFramePacket& Frame, FDetectionResult& OutResult)
	{
		if (CalibrationState != ECalibrationState::Calibrated)
		{
			UE_LOG(LogIIVision, Warning, TEXT("Blob detection called before calibration complete"));
			return;
		}
		
		const int32 NumPixels = Width * Height;
		
		// Ensure we're working with the same size frame
		{
			const bool bIsSameSize = Frame.Width == Width && Frame.Height == Height;
			
			if (!bIsSameSize)
			{
				UE_LOG(LogIIVision, Warning, TEXT("Frame size mismatch. Expected (%d, %d), got (%d, %d)"), Width, Height, Frame.Width, Frame.Height);
				return;
			}
			
			const bool bDataIsSameSize = Frame.Data->Num() == NumPixels * sizeof(uint16);
			
			if (!bDataIsSameSize)
			{
				UE_LOG(LogIIVision, Warning, TEXT("Frame data size mismatch. Expected %llu bytes, got %d"), NumPixels * sizeof(uint16), Frame.Data->Num());
				return;
			}
		}
		
		OutResult.Foreground.SetNumZeroed(NumPixels);
		
		for (int32 i = 0; i < NumPixels; ++i)
		{
			// Get the current depth for this pixel
			const uint16 DepthMm = reinterpret_cast<uint16*>(Frame.Data->GetData())[i];
			
			// Out of range or invalid, skip
			if (DepthMm < DetectionConfig.MinDepthMM || DepthMm > DetectionConfig.MaxDepthMM)
			{
				continue;
			}
			
			// BG was valid, figure out if this pixel is foreground
			if (ValidMask[i])
			{
				// Get the depth for the background
				const uint16 BgDepthMm = BackgroundDepthMm[i];
				const uint16 Delta = FMath::Abs(DepthMm - BgDepthMm);
				
				if (Delta > DetectionConfig.DepthDeltaMM)
				{
					OutResult.Foreground[i] = TNumericLimits<uint8>::Max();
				}
			}
			// BG was invalid, so this pixel is probably foreground
			else
			{
				OutResult.Foreground[i] = TNumericLimits<uint8>::Max();
			}
		}
		
		// Despeckle
		ForegroundScratchBuffer.SetNumUninitialized(NumPixels);
		MajorityFilter(OutResult.Foreground, ForegroundScratchBuffer);
		MajorityFilter(ForegroundScratchBuffer, OutResult.Foreground);
		
		// Find blobs
		ExtractBlobs(OutResult.Foreground, OutResult.ScreenSpaceBlobs);
	}

	void FBlobTracker::EndCalibration()
	{
		ComputeBackground();
		CalibrationFrames.Empty();
	}

	void FBlobTracker::ComputeBackground()
	{
		const int32 NumPixels = Width * Height;
		const int32 NumCalibrationFrames = CalibrationFrames.Num() / NumPixels;
	
		uint16 Samples[MaxCalibrationFrames];
	
		BackgroundDepthMm.SetNumUninitialized(NumPixels);
		ValidMask.SetNumUninitialized(NumPixels);
	
		for (int32 PixelIdx = 0; PixelIdx < NumPixels; ++PixelIdx)
		{
			int32 NumValidSamples = 0;
		
			for (int32 FrameIdx = 0; FrameIdx < NumCalibrationFrames; ++FrameIdx)
			{
				const int32 SampleIdx = PixelIdx + FrameIdx * NumPixels;
				const uint16 DepthMm = CalibrationFrames[SampleIdx];
				if (DepthMm >= CalibrationConfig.MinDepthMM && DepthMm <= CalibrationConfig.MaxDepthMM)
				{
					Samples[NumValidSamples++] = DepthMm;
				}
			}
		
			if (NumValidSamples >= MinFramesValid)
			{
				// Find the median of the valid samples
				std::nth_element(Samples, Samples + NumValidSamples / 2, Samples + NumValidSamples);
				BackgroundDepthMm[PixelIdx] = Samples[NumValidSamples / 2]; 
				ValidMask[PixelIdx] = true;
			}
			else
			{
				BackgroundDepthMm[PixelIdx] = 0;
				ValidMask[PixelIdx] = false;
			}
		}
		
		CalibrationState = ECalibrationState::Calibrated;
	}

	void FBlobTracker::MajorityFilter(const TArray<uint8>& Src, TArray<uint8>& Dst) const
	{
		for (int y = 0; y < Height; ++y)
		{
			for (int x = 0; x < Width; ++x)
			{
				int NumValid = 0;
				
				for (int dy = -1; dy <= 1; ++dy)
				{
					for (int dx = -1; dx <= 1; ++dx)
					{
						const int yTest = y + dy;
						const int xTest = x + dx;
						
						if (yTest < 0 || yTest >= Height || xTest < 0 || xTest >= Width)
						{
							continue;
						}
						
						if (Src[yTest * Width + xTest] > 0)
						{
							++NumValid;
						}
					}
				}
				
				Dst[y * Width + x] = NumValid >= 5 ? TNumericLimits<uint8>::Max() : 0;
			}
		}
	}

	void FBlobTracker::ExtractBlobs(const TArray<uint8>& Foreground, TArray<FBlob2D>& OutBlobs) const
	{
		TBitArray Visited(false, Width * Height);
		TArray<int32> Queue;
		Queue.Reserve(4096); // TODO: figure out max valid blob size
		
		const auto IsFg = [&Foreground](const int32 Idx)
		{
			return Foreground[Idx] > 0;
		};
		
		const auto TryEnqueueNeighbor = [&Visited, &Queue, &IsFg, Width = Width, Height = Height](const int32 X, const int32 Y)
		{
			if (X < 0 || X >= Width || Y < 0 || Y >= Height)
			{
				return;
			}

			if (const int32 Idx = Y * Width + X; !Visited[Idx] && IsFg(Idx))
			{
				Visited[Idx] = true;
				Queue.Add(Idx);
			}
		};
		
		for (int y = 1; y < Height - 1; ++y)
		{
			for (int x = 1; x < Width - 1; ++x)
			{
				const int32 StartIdx = y * Width + x;
				
				if (Visited[StartIdx] || !IsFg(StartIdx))
				{
					continue;
				}
				
				// New blob
				FBlob2D Blob;
				Blob.Id = OutBlobs.Num();
				
				Queue.Reset();
				Queue.Add(StartIdx);
				Visited[StartIdx] = true;
				
				while (!Queue.IsEmpty())
				{
					const int32 Idx = Queue.Pop(EAllowShrinking::No);
					const int32 Cy = Idx / Width;
					const int32 Cx = Idx % Width;
					
					Blob.AddPixel(Cx, Cy);
					
					// Get the 8 neighbors and add them to the blob if valid
					for (int32 Dy = -1; Dy <= 1; ++Dy)
					{
						for (int32 Dx = -1; Dx <= 1; ++Dx)
						{
							TryEnqueueNeighbor(Cx + Dx, Cy + Dy);
						}
					}
				}
				
				if (Blob.PixelCount >= DetectionConfig.MinBlobPixels)
				{
					OutBlobs.Emplace(MoveTemp(Blob));
				}
			}
		}
	}
}
