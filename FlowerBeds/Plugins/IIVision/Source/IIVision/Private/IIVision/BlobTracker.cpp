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

	void FBlobTracker::FBlob2D::AddPixel(const int32 X, const int32 Y)
	{
		++PixelCount;
		MinX = FMath::Min(MinX, X);
		MaxX = FMath::Max(MaxX, X);
		MinY = FMath::Min(MinY, Y);
		MaxY = FMath::Max(MaxY, Y);
		SumX += X;
		SumY += Y;
	}

	FVector2f FBlobTracker::FBlob2D::GetCentroid() const
	{
		const float Inv = PixelCount > 0 ? 1.0f / PixelCount : 0.0f;
		return FVector2f(Inv * SumX, Inv * SumY);
	}

	FVector FBlobTracker::FBlob3D::GetWorldPosCm() const
	{
		// Convert from camera (right, down, forward basis, meters) 
		// to Unreal (forward, right, up basis, centimeters)
		return {
			CamPosMeters.Z * 100,
			CamPosMeters.X * 100,
			-CamPosMeters.Y * 100
		};
	}

	FVector FBlobTracker::FBlob3D::GetWorldHalfExtentsCm() const
	{
		// Convert from camera (right, down, forward basis, meters) 
		// to Unreal (forward, right, up basis, centimeters)
		return {
			CamHalfExtentsMeters.Z * 100,
			CamHalfExtentsMeters.X * 100,
			-CamHalfExtentsMeters.Y * 100
		};
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
		
		// Subtract the background to get the valid foreground
		SubtractBackground(Frame, OutResult);
		
		// Despeckle
		ForegroundScratchBuffer.SetNumUninitialized(NumPixels);
		MajorityFilter(OutResult.Foreground, ForegroundScratchBuffer);
		MajorityFilter(ForegroundScratchBuffer, OutResult.Foreground);
		
		// Find blobs
		ExtractBlobs(OutResult.Foreground, OutResult.ScreenSpaceBlobs);
		Compute3DBlobs(OutResult.ScreenSpaceBlobs, OutResult.WorldSpaceBlobs, Frame.Intrinsics);
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

	void FBlobTracker::SubtractBackground(const FFramePacket& Frame, FDetectionResult& OutResult) const
	{
		const int32 NumPixels = Width * Height;
		
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
				
				// If the bg is closer, skip
				if (BgDepthMm <= DepthMm)
				{
					continue;
				}
				
				const uint16 Delta = BgDepthMm - DepthMm;
				
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

	void FBlobTracker::Compute3DBlobs(
		const TArray<FBlob2D>& ScreenSpaceBlobs, 
		TArray<FBlob3D>& OutBlobs,
		const FCameraIntrinsics& CameraIntrinsics) const
	{
		OutBlobs.Reserve(ScreenSpaceBlobs.Num());
		
		for (const FBlob2D& ScreenSpaceBlob : ScreenSpaceBlobs)
		{
			FBlob3D WorldBlob;
			WorldBlob.Id = ScreenSpaceBlob.Id;
			
			const int32 MinX = FMath::Clamp(ScreenSpaceBlob.MinX, 0, Width - 1);
			const int32 MaxX = FMath::Clamp(ScreenSpaceBlob.MaxX, 0, Width - 1);
			const int32 MinY = FMath::Clamp(ScreenSpaceBlob.MinY, 0, Height - 1);
			const int32 MaxY = FMath::Clamp(ScreenSpaceBlob.MaxY, 0, Height - 1);
			
			// Gather depths, skipping some pixels for speed
			TArray<uint16> Depths;
			const int32 BlobWidth = MaxX - MinX + 1;
			const int32 BlobHeight = MaxY - MinY + 1;
			Depths.Reserve(BlobWidth / DetectionConfig.StridePixels * BlobHeight / DetectionConfig.StridePixels);
			
			for (int32 y = MinY; y <= MaxY; y += DetectionConfig.StridePixels)
			{
				const int32 Row = y * Width;
				
				for (int32 x = MinX; x <= MaxX; x += DetectionConfig.StridePixels)
				{
					const int32 Idx = Row + x;
					const uint16 DepthMm = BackgroundDepthMm[Idx];
					
					if (DepthMm >= DetectionConfig.MinDepthMM && DepthMm <= DetectionConfig.MaxDepthMM)
					{
						Depths.Add(DepthMm);
					}
				}
			}
			
			// Not enough samples in range
			if (Depths.Num() < DetectionConfig.MinSamples)
			{
				continue;
			}
			
			// Find the median depth
			Depths.Sort();
			const uint16 MedianDepthMm = Depths[Depths.Num() / 2];
			WorldBlob.MedianZMeters = MedianDepthMm * 0.001f;
			
			// Find the 3D points within the depth window
			const int32 DepthMinMm = static_cast<int32>(MedianDepthMm) - DetectionConfig.ZWindowMm;
			const int32 DepthMaxMm = static_cast<int32>(MedianDepthMm) + DetectionConfig.ZWindowMm;
			
			FVector Sum(0, 0, 0);
			int32 NumValidPoints = 0;
			
			FVector MinP(FLT_MAX, FLT_MAX, FLT_MAX);
			FVector MaxP(-FLT_MAX, -FLT_MAX, -FLT_MAX);
			
			for (int32 y = MinY; y <= MaxY; y += DetectionConfig.StridePixels)
			{
				const int32 Row = y * Width;
				
				for (int32 x = MinX; x <= MaxX; x += DetectionConfig.StridePixels)
				{
					const int32 Idx = Row + x;
					const uint16 DepthMm = BackgroundDepthMm[Idx];
					
					if (DepthMm < DepthMinMm || DepthMm > DepthMaxMm 
						|| DepthMm < DetectionConfig.MinDepthMM || DepthMm > DetectionConfig.MaxDepthMM)
					{
						continue;
					}
					
					const float Z = DepthMm * 0.001f;
					const FVector P{
						(static_cast<float>(x) - CameraIntrinsics.Cx) * Z / CameraIntrinsics.Fx,
						(static_cast<float>(y) - CameraIntrinsics.Cy) * Z / CameraIntrinsics.Fy,
						Z
					};
					
					Sum += P;
					++NumValidPoints;
					
					MinP.X = FMath::Min(MinP.X, P.X);
					MinP.Y = FMath::Min(MinP.Y, P.Y);
					MinP.Z = FMath::Min(MinP.Z, P.Z);
					MaxP.X = FMath::Max(MaxP.X, P.X);
					MaxP.Y = FMath::Max(MaxP.Y, P.Y);
					MaxP.Z = FMath::Max(MaxP.Z, P.Z);
				}
			}
			
			if (NumValidPoints < DetectionConfig.MinSamples / 2)
			{
				continue;
			}
			
			WorldBlob.CamPosMeters = Sum / NumValidPoints;
			WorldBlob.SampleCount = NumValidPoints;
			WorldBlob.CamHalfExtentsMeters = (MaxP - MinP) * 0.5f;
			WorldBlob.bValid = true;
			
			OutBlobs.Emplace(MoveTemp(WorldBlob));
		}
	}
}
