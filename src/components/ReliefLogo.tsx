import React from 'react';
import Svg, { Circle, Path } from 'react-native-svg';
import { colors } from '../theme';

interface ReliefLogoProps {
  size?: number;
  color?: string;
  accessibilityLabel?: string;
}

/** Native rendering of the approved Relief pin/person/leaf mark. */
export const ReliefLogo: React.FC<ReliefLogoProps> = ({
  size = 56,
  color = colors.primary,
  accessibilityLabel = 'Relief logo',
}) => {
  const cutout = color === '#FFFFFF' ? colors.primary : colors.white;
  const leaf = color === '#FFFFFF' ? colors.sage : colors.primaryLight;

  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      accessibilityRole="image"
      accessibilityLabel={accessibilityLabel}
    >
      <Path d="M32 4C21.5 4 13 12.5 13 23c0 14 19 37 19 37s19-23 19-37C51 12.5 42.5 4 32 4z" fill={color} />
      <Circle cx="32" cy="18" r="4.5" fill={cutout} />
      <Path d="M24 30c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke={cutout} strokeWidth="2.5" strokeLinecap="round" fill="none" />
      <Path d="M34 28c2-3 6-4 9-2-1 4-5 6-9 2z" fill={leaf} />
    </Svg>
  );
};
