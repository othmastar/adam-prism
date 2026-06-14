/**
 * [PHASE5] Tablet/iPad-specific layout for ChatScreen.
 * Two-pane layout: chat list on left, conversation on right.
 */
import { View, Text, StyleSheet, useWindowDimensions, Platform } from "react-native";
import { useEffect } from "react";

interface TabletLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
}

const TABLET_BREAKPOINT = 768;

export function ResponsiveLayout({ children, sidebar, header }: TabletLayoutProps) {
  const { width } = useWindowDimensions();
  const isTablet = width >= TABLET_BREAKPOINT;
  const isLandscape = width > 600;  // Even phones in landscape

  if (isTablet && isLandscape) {
    // [PHASE5] Two-pane tablet layout
    return (
      <View style={styles.tabletContainer}>
        <View style={styles.sidebar}>
          {sidebar}
        </View>
        <View style={styles.main}>
          {header}
          {children}
        </View>
      </View>
    );
  }

  // [PHASE5] Single-pane phone layout
  return (
    <View style={styles.phoneContainer}>
      {header}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  phoneContainer: {
    flex: 1,
  },
  tabletContainer: {
    flex: 1,
    flexDirection: "row",
  },
  sidebar: {
    width: 320,
    borderRightWidth: 1,
    borderRightColor: "#1f2937",
    backgroundColor: "#0a0a0f",
  },
  main: {
    flex: 1,
  },
});
