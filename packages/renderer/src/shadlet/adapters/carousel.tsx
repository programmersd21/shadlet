import * as React from "react";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { cn } from "@/lib/utils";
import { boolean, className, type AdapterProps } from "@/shadlet/types";

export function CarouselAdapter({ props, children }: AdapterProps) {
  const slides = React.Children.toArray(children);
  return (
    <Carousel
      orientation={props.orientation === "vertical" ? "vertical" : "horizontal"}
      opts={{ loop: boolean(props.loop) }}
      className={cn("w-full", className(props))}
    >
      <CarouselContent>
        {slides.map((slide, index) => (
          <CarouselItem key={index}>{slide}</CarouselItem>
        ))}
      </CarouselContent>
      <CarouselPrevious />
      <CarouselNext />
    </Carousel>
  );
}
