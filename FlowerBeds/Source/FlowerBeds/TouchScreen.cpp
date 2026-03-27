#include "TouchScreen.h"

#include "FlowerBeds/FlowerBeds.h"
#include "FlowerBeds/TouchScreenSettings.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"

ATouchScreen::ATouchScreen()
{
	CameraController = CreateDefaultSubobject<UOrbbecCameraController>("CameraController");
}

void ATouchScreen::BeginPlay()
{
	Super::BeginPlay();

	const UTouchScreenSettings* Settings = GetDefault<UTouchScreenSettings>();
	if (!Settings)
	{
		UE_LOG(LogFlowerBeds, Error, TEXT("ATouchScreen: failed to retrieve touch screen settings."));
		return;
	}

	const FTouchScreenConfig* Config = Settings->TouchScreens.FindByPredicate(
		[Name = ScreenName](const FTouchScreenConfig& C)
		{
			return C.Name == Name;
		});

	if (!Config)
	{
		UE_LOG(LogFlowerBeds, Warning,
			TEXT("ATouchScreen: no config found for screen '%s'. Check UTouchScreenSettings."),
			*ScreenName.ToString());
		return;
	}

	// Actor transform tracks the camera position so depth unprojection can use GetActorTransform().
	SetActorLocation(Config->CameraPosCm);
	SetActorRotation(Config->CameraRotation);

	// Store the screen plane as a separate transform.
	ScreenTransform = FTransform(Config->ScreenRotation, Config->ScreenPosCm);
	ScreenWidthCm = Config->WidthCm;
	ScreenHeightCm = Config->HeightCm;
	TouchThresholdCm = Config->TouchThresholdCm;

	CameraController->CameraConfig = Config->CameraConfig;

	check(CameraController);
	OnFramesReceivedDelegateHandle =
		CameraController->OnFramesReceivedNative.AddUObject(this, &ATouchScreen::OnFramesReceived);
	CameraController->StartCamera();
}

void ATouchScreen::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (CameraController)
	{
		CameraController->OnFramesReceivedNative.Remove(OnFramesReceivedDelegateHandle);
	}

	Super::EndPlay(EndPlayReason);
}

void ATouchScreen::SetGrid(int32 Rows, int32 Cols)
{
	GridRows = FMath::Max(1, Rows);
	GridCols = FMath::Max(1, Cols);

	// Fire release events for any currently-touched cells before clearing state.
	for (const int32 CellIndex : TouchedCellIndices)
	{
		FScreenGridCell Cell;
		Cell.Row = CellIndex / GridCols;
		Cell.Col = CellIndex % GridCols;
		OnCellReleased.Broadcast(Cell);
	}

	TouchedCellIndices.Empty();
}

void ATouchScreen::OnFramesReceived(
	const FOrbbecFrame& /* ColorFrame */,
	const FOrbbecFrame& DepthFrame,
	const FOrbbecFrame& /* IRFrame */)
{
	TArray<FVector2D> NormalisedTouches;
	DetectTouches(DepthFrame, NormalisedTouches);
	UpdateTouchedCells(NormalisedTouches);
}

void ATouchScreen::DetectTouches(const FOrbbecFrame& /* DepthFrame */, TArray<FVector2D>& OutNormalisedTouches) const
{
	// TODO: Implement touch detection from the depth frame.
	// See the detailed approach documented in TouchScreen.h.
	OutNormalisedTouches.Reset();
}

bool ATouchScreen::NormalisedPosToCell(const FVector2D& NormPos, FScreenGridCell& OutCell) const
{
	if (NormPos.X < 0.f || NormPos.X > 1.f || NormPos.Y < 0.f || NormPos.Y > 1.f)
	{
		return false;
	}

	// Clamp to the last cell index to handle the exact 1.0 edge.
	OutCell.Row = FMath::Min(static_cast<int32>(NormPos.Y * GridRows), GridRows - 1);
	OutCell.Col = FMath::Min(static_cast<int32>(NormPos.X * GridCols), GridCols - 1);
	return true;
}

void ATouchScreen::UpdateTouchedCells(const TArray<FVector2D>& NormalisedTouches)
{
	TSet<int32> NewTouchedIndices;

	for (const FVector2D& NormPos : NormalisedTouches)
	{
		FScreenGridCell Cell;
		if (!NormalisedPosToCell(NormPos, Cell))
		{
			continue;
		}

		const int32 CellIndex = Cell.Row * GridCols + Cell.Col;
		NewTouchedIndices.Add(CellIndex);

		if (!TouchedCellIndices.Contains(CellIndex))
		{
			OnCellTouched.Broadcast(Cell, NormPos);
		}
	}

	// Fire release events for cells that were touched last frame but not this one.
	for (const int32 CellIndex : TouchedCellIndices)
	{
		if (!NewTouchedIndices.Contains(CellIndex))
		{
			FScreenGridCell Cell;
			Cell.Row = CellIndex / GridCols;
			Cell.Col = CellIndex % GridCols;
			OnCellReleased.Broadcast(Cell);
		}
	}

	TouchedCellIndices = MoveTemp(NewTouchedIndices);
}
