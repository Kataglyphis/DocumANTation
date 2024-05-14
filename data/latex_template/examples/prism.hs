{-# LANGUAGE TemplateHaskell #-}

import Control.Lens

data CanteenMeal = MainCourse String CanteenMeal
                 | Desert String
  deriving Show

meal1 = MainCourse "Sattmacher" (Desert "Pudding")
meal2 = Desert "Yogurt"

makePrisms ''CanteenMeal
-- makeLenses ''CanteenMeal
