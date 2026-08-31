import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.models.communication import (
    CommunicationVersion,
)

from app.models.media_analysis import (
    MediaAnalysis,
    RiskLabel,
)

from app.services.media_analysis import (
    analyze_media_bytes,
)


router = APIRouter(
    prefix="/media",
    tags=["Media Analysis"],
)


@router.post("/analyze")
async def analyze_media(
    file: UploadFile = File(...),
    version_id: int | None = Form(None),
    db: Session = Depends(get_db),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename required.",
        )

    data = await file.read()

    if not data:

        raise HTTPException(
            status_code=400,
            detail="File is empty.",
        )

    try:

        result = analyze_media_bytes(
            data=data,
            filename=file.filename,
            content_type=(
                file.content_type or ""
            ),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Media analysis failed: {exc}",
        )

    database = {
        "stored": False,
    }

    if version_id is not None:

        version = (
            db.query(CommunicationVersion)
            .filter(
                CommunicationVersion.id
                == version_id
            )
            .first()
        )

        if version is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"CommunicationVersion "
                    f"{version_id} not found."
                ),
            )

        risk_label_text = result.get(
            "risk_label",
            "INCONCLUSIVE",
        )

        try:

            risk_label = RiskLabel(
                risk_label_text
            )

        except ValueError:

            risk_label = (
                RiskLabel.INCONCLUSIVE
            )

        analysis = (
            db.query(MediaAnalysis)
            .filter(
                MediaAnalysis.version_id
                == version.id
            )
            .first()
        )

        if analysis is None:

            analysis = MediaAnalysis(
                version_id=version.id,
                risk_score=result.get(
                    "risk_score"
                ),
                risk_label=risk_label,
                model_name=result.get(
                    "model_name",
                    "PramaanScan Multimodal ML",
                ),
                model_version="1.0",
                details=json.dumps(
                    result,
                    default=str,
                ),
                is_advisory=True,
            )

            db.add(analysis)

        else:

            analysis.risk_score = result.get(
                "risk_score"
            )

            analysis.risk_label = risk_label

            analysis.model_name = result.get(
                "model_name",
                "PramaanScan Multimodal ML",
            )

            analysis.details = json.dumps(
                result,
                default=str,
            )

            analysis.is_advisory = True

        db.commit()
        db.refresh(analysis)

        database = {
            "stored": True,
            "media_analysis_id": analysis.id,
            "risk_label": (
                analysis.risk_label.value
            ),
            "risk_score": (
                analysis.risk_score
            ),
            "model_name": (
                analysis.model_name
            ),
            "model_version": (
                analysis.model_version
            ),
            "is_advisory": (
                analysis.is_advisory
            ),
        }

    return {
        "success": True,
        "filename": file.filename,
        "analysis": result,
        "database": database,
    }